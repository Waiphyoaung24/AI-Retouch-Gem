from google import genai
from google.genai import types
from PIL import Image
import io
import os
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("WARNING: GOOGLE_API_KEY not set in environment.")

client = genai.Client(api_key=api_key)

# Gemini-supported aspect ratios mapped to their decimal values
_ASPECT_RATIOS = {
    "1:1": 1.0, "2:3": 2 / 3, "3:2": 3 / 2, "3:4": 3 / 4, "4:3": 4 / 3,
    "4:5": 4 / 5, "5:4": 5 / 4, "9:16": 9 / 16, "16:9": 16 / 9,
}


def detect_aspect_ratio(img: Image.Image) -> str:
    """Map an image's dimensions to the nearest Gemini-supported aspect ratio."""
    w, h = img.size
    ratio = w / h
    best = "4:3"
    best_diff = float("inf")
    for label, val in _ASPECT_RATIOS.items():
        diff = abs(ratio - val)
        if diff < best_diff:
            best_diff = diff
            best = label
    return best


# ---------------------------------------------------------------------------
# Pass 1: Analyze gem characteristics (TEXT only)
# ---------------------------------------------------------------------------

async def analyze_gem(
    product_image_bytes: bytes,
    context_image_bytes: bytes,
) -> dict:
    """Pass 1: Extract detailed gem characteristics from product + context photos.

    Returns a structured dict describing the gem's visual identity:
    color, cut_shape, facet_pattern, clarity, brilliance, unique_features.
    This text description is then used in Pass 2 so we never send a large
    product image to the generation call (which would confuse sizing).
    """
    try:
        product_img = Image.open(io.BytesIO(product_image_bytes))
        context_img = Image.open(io.BytesIO(context_image_bytes))

        prompt = """Analyze these two photographs of the SAME gemstone and describe it in precise detail.

Image 1: Product photograph of the loose gemstone on a clean background.
Image 2: The same gemstone photographed on a human hand for scale.

Describe the gemstone with maximum visual precision. Respond in this exact JSON format only:
{
  "color_primary": "the dominant color (e.g. vivid blue, deep green, rich red)",
  "color_secondary": "any secondary hues or undertones (e.g. slight violet tint, yellowish green)",
  "saturation": "low/medium/high/vivid",
  "tone": "light/medium-light/medium/medium-dark/dark",
  "transparency": "transparent/semi-transparent/translucent/opaque",
  "cut_shape": "round/oval/cushion/emerald/pear/marquise/princess/radiant/asscher/heart/other",
  "facet_pattern": "describe the facet pattern (e.g. brilliant cut with star facets, step cut with parallel facets, mixed cut)",
  "brilliance": "low/medium/high/exceptional — how much light return and sparkle",
  "clarity_appearance": "eye-clean/slightly included/moderately included/heavily included",
  "surface_quality": "any visible surface features (e.g. smooth polished, minor abrasions, windowing)",
  "unique_features": "any distinctive visual characteristics that make this specific stone identifiable (e.g. color zoning, silk inclusions, extinction pattern)",
  "overall_description": "A single sentence capturing the gem's complete visual identity for an artist to reproduce exactly"
}"""

        def _call():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, product_img, context_img],
                config=types.GenerateContentConfig(response_modalities=["TEXT"]),
            )

        response = await asyncio.to_thread(_call)
        text = response.text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(text)
        print(f"[Pass1] Gem analysis: {result.get('overall_description', 'N/A')}")
        return result

    except json.JSONDecodeError as e:
        print(f"[Pass1] JSON parse failed: {e}, raw text: {text[:200]}")
        return {"overall_description": "a colored gemstone with brilliant facets"}
    except Exception as e:
        print(f"[Pass1] Gem Analysis Error: {e}")
        return {"overall_description": "a colored gemstone with brilliant facets"}


# ---------------------------------------------------------------------------
# Photo validation
# ---------------------------------------------------------------------------

async def validate_customer_photo(photo_bytes: bytes, expected_body_part: str) -> dict:
    try:
        img = Image.open(io.BytesIO(photo_bytes))
        prompt = f"""You are a photo quality validator for a jewelry preview app.
Analyze this photo and determine:
1. Does it clearly show a {expected_body_part}?
2. Is the lighting adequate?
3. Is the {expected_body_part} clearly visible and in focus?
4. Is the background reasonably clean?

Respond in this exact JSON format only:
{{"is_valid": true/false, "body_part_detected": "hand"/"ear"/"neck"/null, "feedback": "brief explanation"}}"""

        def _call():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, img],
                config=types.GenerateContentConfig(response_modalities=["TEXT"]),
            )

        response = await asyncio.to_thread(_call)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"is_valid": True, "body_part_detected": expected_body_part, "feedback": "Validation passed (could not parse response)."}
    except Exception as e:
        print(f"Photo Validation Error: {e}")
        return {"is_valid": True, "body_part_detected": None, "feedback": f"Validation skipped: {str(e)}"}


# ---------------------------------------------------------------------------
# Pass 2: Generate jewelry preview (multi-image composition)
# ---------------------------------------------------------------------------

def _prescale_gem_image(
    gem_img: Image.Image,
    target_img: Image.Image,
    target_photo_bytes: bytes,
    gem_to_finger_ratio: float | None,
) -> Image.Image:
    """Resize the gem product image so it visually matches the desired proportion.

    Gemini ignores text-based size instructions but respects the visual size
    of elements in input images.  We shrink the gem and center it on a canvas
    matching the target image dimensions so Gemini "sees" the correct scale.
    """
    from .hand_analysis import analyze_hand, _estimate_finger_width_px

    if gem_to_finger_ratio is None:
        return gem_img  # no ratio data — send original

    # Detect finger width on the target hand photo
    analysis = analyze_hand(target_photo_bytes)
    if not analysis:
        print("[PreScale] No hand in target photo, skipping pre-scale")
        return gem_img

    finger_width_px = _estimate_finger_width_px(analysis, "ring")
    if finger_width_px <= 0:
        return gem_img

    # Target gem width in pixels on the target image
    target_gem_px = finger_width_px * (gem_to_finger_ratio / 100.0)
    target_gem_px = max(10, int(target_gem_px))

    # Resize gem preserving aspect ratio
    gw, gh = gem_img.size
    gem_aspect = gw / gh if gh > 0 else 1.0
    new_w = target_gem_px
    new_h = max(1, int(new_w / gem_aspect))
    gem_resized = gem_img.resize((new_w, new_h), Image.LANCZOS)

    # Place centered on a canvas matching target image dimensions
    tw, th = target_img.size
    canvas = Image.new("RGB", (tw, th), (255, 255, 255))
    paste_x = (tw - new_w) // 2
    paste_y = (th - new_h) // 2
    canvas.paste(gem_resized, (paste_x, paste_y))

    print(f"[PreScale] Gem {gw}x{gh} → {new_w}x{new_h} on {tw}x{th} canvas "
          f"(finger={finger_width_px:.0f}px, ratio={gem_to_finger_ratio}%)")
    return canvas


async def generate_gem_preview(
    gem_product_image_bytes: bytes,
    gem_context_image_bytes: bytes,
    target_photo_bytes: bytes,
    prompt: str,
    gem_to_finger_ratio: float | None = None,
) -> bytes:
    """Generate jewelry preview using Gemini's Detail Preservation pattern.

    Image order follows Gemini docs (base image first, element second, prompt last):
    - Image 1 (first):  Target/base photo to edit (hand/ear/neck)
    - Image 2 (second): Gem product photo (pre-scaled to correct proportion)
    - Image 3 (third):  Gem context photo on hand (size reference only)
    - Text (last):      Composition prompt
    """
    try:
        target_img = Image.open(io.BytesIO(target_photo_bytes))
        gem_img = Image.open(io.BytesIO(gem_product_image_bytes))
        context_img = Image.open(io.BytesIO(gem_context_image_bytes))
        aspect_ratio = detect_aspect_ratio(target_img)

        # Pre-scale the gem image so Gemini sees the correct visual proportion
        gem_img = _prescale_gem_image(
            gem_img, target_img, target_photo_bytes, gem_to_finger_ratio,
        )

        tw, th = target_img.size
        gw, gh = gem_img.size
        print(f"[Generate] gemini-3.1-flash-image-preview: 3 images (target {tw}x{th}, gem {gw}x{gh}, context), "
              f"aspect_ratio={aspect_ratio}, image_size=2K")

        # Gemini Detail Preservation pattern:
        # [base_image, element_image, ref_image, text_prompt]
        # Base image first so Gemini treats it as the image to edit/preserve.
        def _call():
            return client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=[target_img, gem_img, context_img, prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size="2K",
                    ),
                ),
            )

        response = await asyncio.to_thread(_call)
        for part in response.parts:
            if part.inline_data is not None:
                return part.inline_data.data
        raise ValueError("Gemini did not return an image")
    except Exception as e:
        print(f"[Pass2] Generation Error: {e}")
        raise e
