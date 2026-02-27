from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from ..models.schemas import GeneratePreviewResult, PhotoValidationResult
from ..services.gemini_service import (
    generate_gem_preview,
    validate_customer_photo,
)
from ..api.utils import upload_bytes_to_supabase, supabase
import time
import httpx

router = APIRouter()

# ---------------------------------------------------------------------------
# Style & metal detail maps — single source of truth for prompt generation
# ---------------------------------------------------------------------------

METAL_DETAILS = {
    "Gold": "warm yellow gold with rich luster, subtle warm reflections, and polished metallic sheen",
    "White Gold": "white gold with cool silvery brilliance, a hint of warmth, and mirror-polished finish",
    "Rose Gold": "rose gold with soft pinkish-copper warmth, romantic glow, and delicate reflections",
    "Silver": "sterling silver with bright cool luster, crisp highlights, and clean reflections",
    "Platinum": "platinum with dense, cool-white sheen, understated luster, and a weighty appearance",
}

STYLE_DETAILS = {
    # Ring styles
    "Solitaire": "a single center stone held by 4-6 thin prongs on a slim, clean band — minimal, elegant, timeless",
    "Halo": "a center stone encircled by a ring of tiny pavé accent diamonds, adding sparkle and apparent size, on a thin band",
    "Three-Stone": "the center gemstone flanked by two smaller complementary side stones, symbolizing past-present-future, on a slim band",
    "Pavé": "tiny diamonds set closely along the entire band surface, creating continuous micro-sparkle framing the center stone",
    # Earring styles
    "Stud": "the gemstone mounted flush against the earlobe on a secure post backing — compact, refined, everyday elegance",
    "Drop": "the gemstone suspended below the earlobe on a short articulated connector, swaying gently with movement",
    "Hoop": "the gemstone integrated into a slender circular hoop that threads through the ear piercing",
    "Chandelier": "an ornate, tiered design with the gemstone as the focal centerpiece, multiple decorative tiers cascading downward",
    # Pendant styles
    "Bezel": "the gemstone fully encircled by a thin metal rim creating a smooth, modern frame, hanging from a delicate chain",
    "Cluster": "multiple smaller accent stones arranged closely around the center gem, creating a floral or starburst pattern on a chain",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def fetch_image_bytes(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to fetch image from {url}")
        return response.content


def _build_size_anchor(
    category_name: str,
    carat: float,
    length_mm,
    width_mm,
    dim_text: str,
    gem_to_finger_ratio: float | None = None,
) -> str:
    """Generate size instructions referencing the correct images.

    When gem_to_finger_ratio is available (4-image mode):
      Image 3 = pre-scaled gem on canvas (size reference)
      Image 4 = context photo (gem on real hand, backup confirmation)
    When missing (3-image mode):
      Image 3 = context photo (gem on real hand)
    """
    AVG_FINGER_WIDTH_MM = 16.0
    has_ratio = gem_to_finger_ratio is not None

    # --- Determine percentage ---
    if has_ratio:
        pct = round(gem_to_finger_ratio)
        ratio_desc = (
            f"The gem should appear approximately {pct}% of the finger's width — "
        )
    else:
        gem_w = float(width_mm) if width_mm else float(length_mm) if length_mm else None
        if gem_w:
            pct = round((gem_w / AVG_FINGER_WIDTH_MM) * 100)
            ratio_desc = (
                f"The gem is {gem_w}mm wide. An average finger is about {AVG_FINGER_WIDTH_MM:.0f}mm wide. "
                f"So the gem should appear approximately {pct}% of the finger's width — "
            )
        else:
            pct = None
            ratio_desc = f"The gem is {dim_text}. "

    if pct is not None:
        if pct <= 35:
            ratio_desc += "it is a SMALL stone, noticeably smaller than the finger width. Do NOT enlarge it."
        elif pct <= 60:
            ratio_desc += "it is a medium stone, roughly half the finger width."
        else:
            ratio_desc += "it is a large stone, approaching the finger width."

    # Visual size references differ based on 4-image vs 3-image mode
    if has_ratio:
        visual_ref = (
            f"The third image shows how large the gem should appear relative to the hand — "
            f"match that exact size. The fourth image confirms this proportion on a real hand. "
            f"Do not make the gem bigger than shown."
        )
    else:
        visual_ref = (
            f"The third image shows this exact gem on a real hand. "
            f"The gem in your output MUST appear at the same proportion relative to the finger "
            f"as it does in the third image. Do not make it bigger."
        )

    if category_name == "Ring":
        return f"{ratio_desc} {visual_ref}"
    elif category_name == "Earring":
        return (
            f"{ratio_desc} "
            f"An earlobe is roughly the same width as a finger, so render the gem at this same "
            f"proportion relative to the earlobe. {visual_ref}"
        )
    else:  # Pendant
        return (
            f"{ratio_desc} "
            f"A human chest is much wider than a hand, so the gem will look proportionally SMALLER "
            f"as a pendant. A {dim_text} gem is a small, delicate pendant. {visual_ref}"
        )


def _wear_instruction(category_name: str) -> str:
    if category_name == "Ring":
        return "the band wraps around the finger with the gem sitting on top, like a real person wearing a ring"
    elif category_name == "Earring":
        return "the earring hangs naturally from or sits on the earlobe, like real jewelry being worn"
    else:
        return "the pendant hangs from a delicate chain around the neck, resting naturally on the chest"


def build_prompt(
    category_name: str,
    metal_name: str,
    style_name: str,
    gem_data: dict = None,
    finger: Optional[str] = None,
) -> str:
    """Build prompt for the 4-image (or 3-image fallback) pipeline.

    4-image mode (when gem_to_finger_ratio exists):
      Image 1: target hand  |  Image 2: full-res gem (fidelity)
      Image 3: pre-scaled gem (size)  |  Image 4: context photo (confirmation)

    3-image fallback (no ratio):
      Image 1: target hand  |  Image 2: full-res gem  |  Image 3: context photo
    """
    gem_data = gem_data or {}
    body_part = "hand" if category_name == "Ring" else "ear" if category_name == "Earring" else "neck"
    finger_name = finger if finger else "ring"
    placement = f"{finger_name} finger" if category_name == "Ring" else "earlobe" if category_name == "Earring" else "neck/chest"

    # Dimension context as natural language
    carat = gem_data.get("carat_weight")
    length = gem_data.get("length_mm")
    width = gem_data.get("width_mm")
    dim_parts = []
    if carat:
        dim_parts.append(f"{carat} carats")
    if length and width:
        dim_parts.append(f"approximately {length} x {width} mm")
    dim_text = ", ".join(dim_parts) if dim_parts else "a small gemstone"

    metal_desc = METAL_DETAILS.get(metal_name, f"{metal_name.lower()} metal with realistic reflections")
    style_desc = STYLE_DETAILS.get(style_name, f"a {style_name.lower()} setting")

    # Size anchors — prefer measured ratio from DB, fall back to mm computation
    carat_f = float(carat) if carat else 1.0
    size_anchor = _build_size_anchor(
        category_name, carat_f, length, width, dim_text,
        gem_to_finger_ratio=gem_data.get("gem_to_finger_ratio"),
    )

    return f"""Take the first image of a person's {body_part}. Place a gemstone onto the {placement} in a {style_name} {category_name.lower()} setting made of {metal_desc}. Ensure that the person's {body_part}, skin texture, skin tone, pose, and background in the first image remain completely unchanged.

CRITICAL — GEM VISUAL FIDELITY: The second image is a high-resolution close-up of the exact gemstone. You MUST reproduce this gem with pixel-perfect fidelity — identical color, identical shape, identical cut, identical facet pattern, identical brilliance, identical inclusions. Do not reimagine, simplify, or recreate the gem. Every visual detail from the second image must be preserved exactly.

SIZE — MATCH THE REFERENCE:
{size_anchor}

The {style_name} setting: {style_desc}. The jewelry must be worn naturally — {_wear_instruction(category_name)}.

The {metal_name.lower()} setting should have realistic reflections and cast a subtle shadow where it contacts the skin. Match the lighting direction and color temperature from the first image. Output only the final photograph with no text or labels."""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/validate-photo", response_model=PhotoValidationResult)
async def validate_photo(photo: UploadFile = File(...), body_part: str = Form(...)):
    photo_bytes = await photo.read()
    result = await validate_customer_photo(photo_bytes, body_part)
    return PhotoValidationResult(**result)


@router.post("/generate", response_model=GeneratePreviewResult)
async def generate_preview(
    gem_id: str = Form(...),
    category_id: str = Form(...),
    metal_id: str = Form(...),
    style_id: str = Form(...),
    model_photo_id: Optional[str] = Form(None),
    customer_photo: Optional[UploadFile] = File(None),
    finger: Optional[str] = Form(None),
):
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Supabase not configured")

        start_time = time.time()

        # 1. Fetch gem data + both images
        gem_res = supabase.table("gems").select("*").eq("id", gem_id).single().execute()
        if not gem_res.data:
            raise HTTPException(status_code=404, detail="Gem not found")

        gem_data = gem_res.data
        gem_image_bytes = await fetch_image_bytes(gem_data["product_image_url"])
        context_image_bytes = await fetch_image_bytes(gem_data["context_image_url"])

        # 2. Get target photo
        if model_photo_id:
            mp_res = supabase.table("model_photos").select("*").eq("id", model_photo_id).single().execute()
            if not mp_res.data:
                raise HTTPException(status_code=404, detail="Model photo not found")
            target_photo_bytes = await fetch_image_bytes(mp_res.data["image_url"])
        elif customer_photo:
            target_photo_bytes = await customer_photo.read()
        else:
            raise HTTPException(status_code=400, detail="Either model_photo_id or customer_photo required")

        # 3. Resolve setting names
        cat_res = supabase.table("setting_categories").select("name, body_part").eq("id", category_id).single().execute()
        met_res = supabase.table("metals").select("name").eq("id", metal_id).single().execute()
        sty_res = supabase.table("setting_styles").select("name").eq("id", style_id).single().execute()
        category_name = cat_res.data["name"] if cat_res.data else "Ring"
        body_part = cat_res.data.get("body_part", "hand") if cat_res.data else "hand"
        metal_name = met_res.data["name"] if met_res.data else "Gold"
        style_name = sty_res.data["name"] if sty_res.data else "Solitaire"

        # ---------------------------------------------------------------
        # Generate jewelry preview (multi-image composition)
        # ---------------------------------------------------------------
        print(f"[Generate] Building prompt and generating preview...")
        prompt_text = build_prompt(
            category_name, metal_name, style_name,
            gem_data=gem_data,
            finger=finger,
        )

        result_bytes = await generate_gem_preview(
            gem_product_image_bytes=gem_image_bytes,
            gem_context_image_bytes=context_image_bytes,
            target_photo_bytes=target_photo_bytes,
            prompt=prompt_text,
            gem_to_finger_ratio=gem_data.get("gem_to_finger_ratio"),
        )

        processing_time = (time.time() - start_time) * 1000
        print(f"[Generate] Done in {processing_time:.0f}ms")

        # 5. Upload result
        result_url = await upload_bytes_to_supabase(result_bytes, "results")

        return GeneratePreviewResult(result_url=result_url, processing_time_ms=processing_time)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
