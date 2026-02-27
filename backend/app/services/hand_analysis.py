"""Hand landmark detection, scale calibration, and ring compositing using MediaPipe + Pillow."""

import io
import math
import asyncio
import json
import os
import urllib.request
import numpy as np
from dataclasses import dataclass
from typing import Optional

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options as mp_base_options
from PIL import Image, ImageDraw, ImageFilter

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
_gemini_client = genai.Client(api_key=api_key) if api_key else None

# ---------------------------------------------------------------------------
# Model download + HandLandmarker singleton
# ---------------------------------------------------------------------------

_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")
_MODEL_PATH = os.path.join(_MODEL_DIR, "hand_landmarker.task")

_hand_landmarker: Optional[vision.HandLandmarker] = None


def _get_hand_landmarker() -> vision.HandLandmarker:
    """Get or create the HandLandmarker singleton (downloads model on first use)."""
    global _hand_landmarker
    if _hand_landmarker is not None:
        return _hand_landmarker

    # Download model if needed
    os.makedirs(_MODEL_DIR, exist_ok=True)
    if not os.path.exists(_MODEL_PATH):
        print("[HandAnalysis] Downloading hand_landmarker model...")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print("[HandAnalysis] Model downloaded.")

    options = vision.HandLandmarkerOptions(
        base_options=mp_base_options.BaseOptions(model_asset_path=_MODEL_PATH),
        running_mode=vision.RunningMode.IMAGE,
        num_hands=1,
        min_hand_detection_confidence=0.3,
        min_hand_presence_confidence=0.3,
    )
    _hand_landmarker = vision.HandLandmarker.create_from_options(options)
    print("[HandAnalysis] HandLandmarker initialized.")
    return _hand_landmarker


# ---------------------------------------------------------------------------
# Landmark indices
# ---------------------------------------------------------------------------

WRIST = 0
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

# Finger definitions: (name, MCP, PIP, DIP, TIP)
FINGERS = [
    ("index", INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP),
    ("middle", MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP),
    ("ring", RING_MCP, RING_PIP, RING_DIP, RING_TIP),
    ("pinky", PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP),
]

# Metal band colors (RGBA)
METAL_COLORS = {
    "Gold": (202, 138, 4, 255),
    "White Gold": (192, 192, 192, 255),
    "Rose Gold": (183, 110, 121, 255),
    "Silver": (170, 169, 173, 255),
    "Platinum": (200, 200, 210, 255),
}

DEFAULT_FINGER_WIDTH_MM = 17.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Landmark:
    x: float  # normalized [0, 1]
    y: float
    z: float


@dataclass
class HandAnalysis:
    landmarks: list[Landmark]
    handedness: str
    confidence: float
    image_width: int
    image_height: int


@dataclass
class FingerPosition:
    finger_name: str
    x: float
    y: float
    angle: float
    landmark_pip: int
    landmark_dip: int


@dataclass
class ScaleInfo:
    mm_per_pixel: float
    finger_width_mm: float
    finger_width_px: float


@dataclass
class RingPreviewData:
    preview_image_bytes: bytes
    fingers: list[dict]
    scale_info: dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bytes_to_pil(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes))


def _bytes_to_mp_image(image_bytes: bytes) -> tuple[mp.Image, int, int]:
    """Convert raw image bytes to a MediaPipe Image + dimensions."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    cv2_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    h, w, _ = cv2_img.shape
    rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    return mp_image, w, h


# ---------------------------------------------------------------------------
# Hand detection (Tasks API)
# ---------------------------------------------------------------------------

def analyze_hand(image_bytes: bytes) -> Optional[HandAnalysis]:
    """Run MediaPipe HandLandmarker on an image and return landmarks."""
    try:
        mp_image, w, h = _bytes_to_mp_image(image_bytes)
    except Exception as e:
        print(f"[HandAnalysis] Image decode failed: {e}")
        return None

    landmarker = _get_hand_landmarker()
    result = landmarker.detect(mp_image)

    if not result.hand_landmarks:
        return None

    hand_lms = result.hand_landmarks[0]
    landmarks = [
        Landmark(x=lm.x, y=lm.y, z=lm.z)
        for lm in hand_lms
    ]

    handedness = "Right"
    confidence = 0.0
    if result.handedness:
        cls = result.handedness[0][0]
        handedness = cls.category_name
        confidence = cls.score

    return HandAnalysis(
        landmarks=landmarks,
        handedness=handedness,
        confidence=confidence,
        image_width=w,
        image_height=h,
    )


# ---------------------------------------------------------------------------
# Finger positions for tap targets
# ---------------------------------------------------------------------------

def get_finger_positions(analysis: HandAnalysis) -> list[FingerPosition]:
    """Extract the ring placement point (PIP-DIP midpoint) for each finger."""
    positions = []
    lms = analysis.landmarks
    w, h = analysis.image_width, analysis.image_height

    for name, mcp_idx, pip_idx, dip_idx, tip_idx in FINGERS:
        pip_lm = lms[pip_idx]
        dip_lm = lms[dip_idx]

        cx = ((pip_lm.x + dip_lm.x) / 2) * w
        cy = ((pip_lm.y + dip_lm.y) / 2) * h

        dx = (dip_lm.x * w) - (pip_lm.x * w)
        dy = (dip_lm.y * h) - (pip_lm.y * h)
        angle = math.degrees(math.atan2(dy, dx))

        positions.append(FingerPosition(
            finger_name=name,
            x=cx,
            y=cy,
            angle=angle,
            landmark_pip=pip_idx,
            landmark_dip=dip_idx,
        ))

    return positions


def _estimate_finger_width_px(analysis: HandAnalysis, finger_name: str = "ring") -> float:
    """Estimate finger width in pixels using adjacent MCP joint spacing.

    Finger width ~ 65% of the distance between adjacent MCP joints.
    """
    lms = analysis.landmarks
    w, h = analysis.image_width, analysis.image_height

    def _dist(a_idx: int, b_idx: int) -> float:
        return math.hypot(
            (lms[a_idx].x - lms[b_idx].x) * w,
            (lms[a_idx].y - lms[b_idx].y) * h,
        )

    if finger_name == "ring":
        avg_spacing = (_dist(RING_MCP, MIDDLE_MCP) + _dist(RING_MCP, PINKY_MCP)) / 2
    elif finger_name == "index":
        avg_spacing = _dist(INDEX_MCP, MIDDLE_MCP)
    elif finger_name == "middle":
        avg_spacing = (_dist(MIDDLE_MCP, INDEX_MCP) + _dist(MIDDLE_MCP, RING_MCP)) / 2
    elif finger_name == "pinky":
        avg_spacing = _dist(PINKY_MCP, RING_MCP)
    else:
        avg_spacing = 40.0

    return avg_spacing * 0.65


# ---------------------------------------------------------------------------
# Scale calibration using context image
# ---------------------------------------------------------------------------

async def _detect_gem_bbox_with_gemini(context_image_bytes: bytes) -> Optional[dict]:
    """Use Gemini Flash to locate the gem bounding box in the context image."""
    if not _gemini_client:
        return None

    img = Image.open(io.BytesIO(context_image_bytes))
    w, h = img.size

    prompt = (
        "Look at this image of a gemstone on or near a human hand. "
        "Locate the gemstone and return its bounding box as pixel coordinates. "
        f"The image dimensions are {w}x{h} pixels.\n\n"
        'Return ONLY this JSON format, no other text:\n'
        '{"x_min": <int>, "y_min": <int>, "x_max": <int>, "y_max": <int>}'
    )

    try:
        def _call():
            return _gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, img],
                config=types.GenerateContentConfig(response_modalities=["TEXT"]),
            )

        response = await asyncio.to_thread(_call)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        bbox = json.loads(text)
        print(f"[HandAnalysis] Gem bbox detected: {bbox}")
        return bbox
    except Exception as e:
        print(f"[HandAnalysis] Gem bbox detection failed: {e}")
        return None


async def measure_gem_to_finger_ratio(context_image_bytes: bytes) -> float | None:
    """Measure the gem's width as a percentage of finger width using MediaPipe + Gemini bbox.

    1. MediaPipe detects hand landmarks → compute middle finger width in pixels
    2. Gemini Flash locates the gem bounding box → gem width in pixels
    3. ratio = (gem_width_px / finger_width_px) * 100

    Returns the ratio as a float (e.g. 30.0 meaning 30%), or None on failure.
    """
    analysis = analyze_hand(context_image_bytes)
    if not analysis:
        print("[Ratio] No hand detected in context image")
        return None

    finger_width_px = _estimate_finger_width_px(analysis, "middle")
    if finger_width_px <= 0:
        print("[Ratio] Invalid finger width")
        return None

    bbox = await _detect_gem_bbox_with_gemini(context_image_bytes)
    if not bbox:
        print("[Ratio] Could not detect gem bounding box")
        return None

    gem_width_px = bbox["x_max"] - bbox["x_min"]
    gem_height_px = bbox["y_max"] - bbox["y_min"]
    gem_major_px = max(gem_width_px, gem_height_px)

    if gem_major_px <= 0:
        print("[Ratio] Invalid gem dimensions from bbox")
        return None

    ratio = (gem_major_px / finger_width_px) * 100
    ratio = round(ratio, 1)
    print(f"[Ratio] MediaPipe+bbox: gem={gem_major_px:.0f}px, finger={finger_width_px:.0f}px → {ratio}%")
    return ratio


async def calibrate_scale(
    context_image_bytes: bytes,
    gem_length_mm: Optional[float],
    gem_width_mm: Optional[float],
) -> ScaleInfo:
    """Calibrate mm-per-pixel using the context image (gem on hand).

    Strategy: Gemini bbox detection for mm_per_pixel (independent of hand detection),
    then optionally use hand analysis for finger width estimation.
    """
    analysis = analyze_hand(context_image_bytes)
    print(f"[HandAnalysis] Context image hand detection: {'found' if analysis else 'no hand detected'}")

    # Attempt Gemini bbox detection whenever gem dimensions are known
    mm_per_pixel = None
    if gem_length_mm and gem_width_mm:
        bbox = await _detect_gem_bbox_with_gemini(context_image_bytes)
        if bbox:
            gem_px_w = bbox["x_max"] - bbox["x_min"]
            gem_px_h = bbox["y_max"] - bbox["y_min"]

            if gem_px_w > 0 and gem_px_h > 0:
                gem_px_major = max(gem_px_w, gem_px_h)
                gem_mm_major = max(gem_length_mm, gem_width_mm)
                mm_per_pixel = gem_mm_major / gem_px_major

    # Compute finger width from hand analysis or derive from mm_per_pixel
    if analysis:
        finger_width_px = _estimate_finger_width_px(analysis, "ring")
        if mm_per_pixel:
            finger_width_mm = finger_width_px * mm_per_pixel
        else:
            finger_width_mm = DEFAULT_FINGER_WIDTH_MM
            mm_per_pixel = finger_width_mm / finger_width_px
    else:
        # No hand in context image — use defaults
        if mm_per_pixel:
            finger_width_mm = DEFAULT_FINGER_WIDTH_MM
            finger_width_px = finger_width_mm / mm_per_pixel
        else:
            finger_width_px = 40.0
            finger_width_mm = DEFAULT_FINGER_WIDTH_MM
            mm_per_pixel = finger_width_mm / finger_width_px

    method = "gem bbox" if (gem_length_mm and gem_width_mm and mm_per_pixel != DEFAULT_FINGER_WIDTH_MM / 40.0) else "fallback"
    print(f"[HandAnalysis] Calibrated ({method}): {mm_per_pixel:.4f} mm/px, "
          f"finger width: {finger_width_mm:.1f}mm ({finger_width_px:.0f}px)")

    return ScaleInfo(
        mm_per_pixel=mm_per_pixel,
        finger_width_mm=finger_width_mm,
        finger_width_px=finger_width_px,
    )


# ---------------------------------------------------------------------------
# Gem background removal
# ---------------------------------------------------------------------------

def _remove_gem_background(gem_img: Image.Image) -> Image.Image:
    """Remove white/light background from gem product photo using threshold masking."""
    rgba = gem_img.convert("RGBA")
    data = np.array(rgba)

    r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    brightness = (r.astype(int) + g.astype(int) + b.astype(int)) / 3

    mask = np.ones(brightness.shape, dtype=np.float32)
    mask[brightness > 240] = 0.0
    high_band = (brightness > 220) & (brightness <= 240)
    mask[high_band] = (240 - brightness[high_band].astype(float)) / 20.0

    data[:, :, 3] = (mask * 255).astype(np.uint8)
    result = Image.fromarray(data)

    alpha = result.split()[3]
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=1))
    result.putalpha(alpha)

    return result


# ---------------------------------------------------------------------------
# Ring compositing
# ---------------------------------------------------------------------------

def composite_ring_preview(
    customer_image_bytes: bytes,
    gem_image_bytes: bytes,
    scale_info: ScaleInfo,
    metal_name: str = "Gold",
    finger_index: int = 2,
) -> Optional[RingPreviewData]:
    """Composite a ring preview onto the customer's hand photo."""
    analysis = analyze_hand(customer_image_bytes)
    if not analysis:
        return None

    finger_positions = get_finger_positions(analysis)
    if finger_index >= len(finger_positions):
        finger_index = 2

    target_finger = finger_positions[finger_index]

    customer_finger_width_px = _estimate_finger_width_px(
        analysis, target_finger.finger_name
    )

    # Load images
    customer_img = _bytes_to_pil(customer_image_bytes).convert("RGBA")
    gem_img = _bytes_to_pil(gem_image_bytes)
    gem_clean = _remove_gem_background(gem_img)

    # Scale gem relative to finger width
    gw, gh = gem_clean.size
    gem_aspect = gw / gh if gh > 0 else 1.0
    gem_render_w = max(1, int(customer_finger_width_px * 0.85))
    gem_render_h = max(1, int(gem_render_w / gem_aspect))

    gem_scaled = gem_clean.resize((gem_render_w, gem_render_h), Image.LANCZOS)

    # Rotate gem perpendicular to finger direction
    rotation_angle = -(target_finger.angle - 90)
    gem_rotated = gem_scaled.rotate(rotation_angle, expand=True, resample=Image.BICUBIC)

    composite = customer_img.copy()

    # Draw metallic band
    _draw_ring_band(composite, target_finger, customer_finger_width_px, metal_name)

    # Place gem centered on the band with slight upward offset
    cx, cy = int(target_finger.x), int(target_finger.y)
    finger_dir_x = math.cos(math.radians(target_finger.angle))
    finger_dir_y = math.sin(math.radians(target_finger.angle))
    perp_x = -finger_dir_y
    perp_y = finger_dir_x
    offset = gem_render_h * 0.15
    gem_cx = cx + int(perp_x * offset)
    gem_cy = cy + int(perp_y * offset)

    paste_x = gem_cx - gem_rotated.width // 2
    paste_y = gem_cy - gem_rotated.height // 2

    composite.paste(gem_rotated, (paste_x, paste_y), gem_rotated)

    # Export
    output = io.BytesIO()
    composite.convert("RGB").save(output, format="PNG", quality=95)
    preview_bytes = output.getvalue()

    # Return normalized (0-1) coordinates so the frontend can use percentages
    fingers_data = [
        {
            "finger_name": fp.finger_name,
            "x": round(fp.x / analysis.image_width, 4),
            "y": round(fp.y / analysis.image_height, 4),
            "angle": round(fp.angle, 1),
            "is_active": i == finger_index,
        }
        for i, fp in enumerate(finger_positions)
    ]

    scale_data = {
        "mm_per_pixel": round(scale_info.mm_per_pixel, 4),
        "finger_width_mm": round(scale_info.finger_width_mm, 1),
        "finger_width_px": round(customer_finger_width_px, 1),
    }

    return RingPreviewData(
        preview_image_bytes=preview_bytes,
        fingers=fingers_data,
        scale_info=scale_data,
    )


def _draw_ring_band(
    img: Image.Image,
    finger: FingerPosition,
    finger_width_px: float,
    metal_name: str,
):
    """Draw a metallic ring band across the finger at the placement point."""
    draw = ImageDraw.Draw(img)
    color = METAL_COLORS.get(metal_name, METAL_COLORS["Gold"])

    cx, cy = finger.x, finger.y
    angle_rad = math.radians(finger.angle)

    band_thickness = max(3, int(finger_width_px * 0.15))
    half_width = finger_width_px / 2

    perp_x = -math.sin(angle_rad)
    perp_y = math.cos(angle_rad)

    x1 = cx + perp_x * half_width
    y1 = cy + perp_y * half_width
    x2 = cx - perp_x * half_width
    y2 = cy - perp_y * half_width

    draw.line([(x1, y1), (x2, y2)], fill=color[:3], width=band_thickness)

    # Highlight for metallic sheen
    highlight = tuple(min(255, c + 40) for c in color[:3])
    draw.line([(x1, y1), (x2, y2)], fill=highlight, width=max(1, band_thickness // 3))
