from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from ..models.schemas import GeneratePreviewResult, PhotoValidationResult
from ..services.gemini_service import (
    analyze_gem,
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


def _format_gem_description(gem_analysis: dict) -> str:
    """Format the Pass 1 analysis into a rich text block for the Pass 2 prompt."""
    parts = []

    overall = gem_analysis.get("overall_description")
    if overall:
        parts.append(f"Overall: {overall}")

    color = gem_analysis.get("color_primary", "")
    secondary = gem_analysis.get("color_secondary", "")
    if color:
        color_str = color
        if secondary and secondary.lower() not in ("none", "n/a", ""):
            color_str += f" with {secondary}"
        parts.append(f"Color: {color_str}")

    sat = gem_analysis.get("saturation")
    tone = gem_analysis.get("tone")
    if sat and tone:
        parts.append(f"Saturation/tone: {sat} saturation, {tone} tone")

    cut = gem_analysis.get("cut_shape")
    if cut:
        parts.append(f"Cut shape: {cut}")

    facets = gem_analysis.get("facet_pattern")
    if facets:
        parts.append(f"Facet pattern: {facets}")

    brilliance = gem_analysis.get("brilliance")
    if brilliance:
        parts.append(f"Brilliance: {brilliance}")

    transparency = gem_analysis.get("transparency")
    if transparency:
        parts.append(f"Transparency: {transparency}")

    unique = gem_analysis.get("unique_features")
    if unique and unique.lower() not in ("none", "n/a", ""):
        parts.append(f"Unique features: {unique}")

    return "\n".join(parts)


def _build_size_anchor(category_name: str, carat: float, length_mm, width_mm, dim_text: str) -> str:
    """Generate a size description that defers to the visual context image (Image 2) as ground truth."""

    body_ref = "finger" if category_name == "Ring" else "earlobe" if category_name == "Earring" else "neck"

    return (
        f"The gemstone is {dim_text}. "
        f"Image 2 shows this EXACT gem on a real human {body_ref} — use that photo as your size reference. "
        f"The gem in your output on the {body_ref} in Image 3 must be the SAME size relative to the {body_ref} "
        f"as it appears in Image 2. Do not enlarge or shrink it."
    )


def build_prompt(
    category_name: str,
    metal_name: str,
    style_name: str,
    gem_data: dict = None,
    gem_description: str = "",
) -> str:
    """Build the Pass 2 generation prompt using Gemini's multi-image composition pattern.

    Follows the 'Advanced Composition' and 'High-fidelity detail preservation'
    templates from the Gemini docs — narrative description, not a list of rules.
    """
    gem_data = gem_data or {}
    body_part = "hand" if category_name == "Ring" else "ear" if category_name == "Earring" else "neck"
    placement = "ring finger" if category_name == "Ring" else "earlobe" if category_name == "Earring" else "neck/chest"

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

    # Size anchors scaled by carat weight — an average adult finger is ~16mm wide
    carat_f = float(carat) if carat else 1.0
    size_anchor = _build_size_anchor(category_name, carat_f, length, width, dim_text)

    return f"""Create a photorealistic jewelry product photograph.

You are given three reference images:
- Image 1: A loose gemstone product photo — use it as the visual reference for the gem's exact color, cut, facets, and brilliance.
- Image 2: The SAME gemstone photographed on a real human {body_part} — use this as your SIZE reference. The gem-to-{body_part} proportion in this photo is the ground truth.
- Image 3: A person's {body_part} — this is the base photograph. Keep this image exactly as-is except for adding the jewelry.

GEMSTONE VISUAL IDENTITY (preserve these exact visual qualities from Image 1):
{gem_description}

COMPOSITION TASK:
Place the gemstone from Image 1 into a {style_name} {category_name.lower()} setting made of {metal_desc}. The {category_name.lower()} must be WORN on the {placement} of the person in Image 3 — the band wraps around the finger with the gem sitting on top, just like a real person wearing a ring. Do NOT place the jewelry floating in the air or detached from the body.

SIZE — MATCH IMAGE 2 EXACTLY:
{size_anchor}

SETTING DESIGN:
{style_desc}

PHOTOGRAPHIC QUALITY:
Render this as a professional jewelry advertisement photograph. The person's skin texture, skin tone, pose, and the entire background must remain exactly as they appear in Image 3. Match the lighting direction and color temperature from Image 3. The {metal_name.lower()} setting should have realistic reflections and cast a subtle shadow where it contacts the skin. The gemstone must faithfully reproduce the exact color, cut shape, facet pattern, and brilliance visible in Image 1. Output only the final photograph with no text or labels."""


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
        # PASS 1: Analyze gem characteristics (TEXT only, fast)
        # ---------------------------------------------------------------
        print(f"[Generate] Pass 1: Analyzing gem characteristics...")
        gem_analysis = await analyze_gem(gem_image_bytes, context_image_bytes)
        gem_description = _format_gem_description(gem_analysis)
        pass1_time = time.time() - start_time
        print(f"[Generate] Pass 1 done in {pass1_time:.1f}s")

        # ---------------------------------------------------------------
        # PASS 2: Generate jewelry preview (multi-image composition)
        # ---------------------------------------------------------------
        print(f"[Generate] Pass 2: Generating jewelry preview...")
        prompt_text = build_prompt(
            category_name, metal_name, style_name,
            gem_data=gem_data,
            gem_description=gem_description,
        )

        result_bytes = await generate_gem_preview(
            gem_product_image_bytes=gem_image_bytes,
            gem_context_image_bytes=context_image_bytes,
            target_photo_bytes=target_photo_bytes,
            prompt=prompt_text,
        )

        processing_time = (time.time() - start_time) * 1000
        print(f"[Generate] Both passes done in {processing_time:.0f}ms")

        # 5. Upload result
        result_url = await upload_bytes_to_supabase(result_bytes, "results")

        return GeneratePreviewResult(result_url=result_url, processing_time_ms=processing_time)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
