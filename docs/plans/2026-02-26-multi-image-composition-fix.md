# Multi-Image Composition Fix — Gemini Image Generation Quality

**Date:** 2026-02-26
**Status:** Ready for implementation
**Problem:** Customer-uploaded hand photos produce bad jewelry previews
**Solution:** Switch from pre-composite to Gemini's native multi-image composition pattern

---

## Problem Analysis

The current two-pass architecture has a fundamental flaw in Pass 2:

1. **Pre-composite looks fake**: PIL-pasting a flat gem onto a hand photo creates an unnatural input that Gemini can't make realistic
2. **Prompt is rules-heavy**: 8 strict RULES instead of the narrative descriptions Gemini docs recommend
3. **Missing gem visual reference**: We removed the gem product photo from Pass 2 (to fix sizing) so Gemini has no visual reference for the gem's exact appearance

## Solution: Multi-Image Composition Pattern

Based on the official Gemini docs' "Advanced Composition" pattern (dress+model example), we switch to:

```
contents = [gem_product_photo, customer_hand_photo, narrative_prompt]
```

This is the exact same pattern Google demonstrates for combining a product (dress) with a person (model) — we combine a product (gem) with a person's body part (hand/ear/neck).

**Key Gemini doc principles applied:**
- "Describe the scene, don't just list keywords" — narrative prompts
- "High-fidelity detail preservation" — describe the gem in detail, tell Gemini what to preserve
- "Advanced composition" — send both reference images, let Gemini handle composition
- `image_config` with aspect ratio — match output to input photo orientation

---

## Architecture Changes

### Before (current)
```
Pass 1: [product_img, context_img] → gemini-2.5-flash (TEXT) → gem_description
Pass 2: PIL pre-composite(gem, hand) → [composite, rules_prompt] → gemini-2.5-flash-image → result
```

### After (new)
```
Pass 1: [product_img, context_img] → gemini-2.5-flash (TEXT) → gem_description  (unchanged)
Pass 2: [product_img, hand_photo, narrative_prompt] → gemini-2.5-flash-image → result
```

- Pass 1 stays identical — it produces the gem visual identity text
- Pass 2 changes completely — no pre-composite, send both images, narrative prompt
- Pre-compositing pipeline (estimate_pixels_per_mm, create_pre_composite) is removed

---

## Implementation Tasks

### Task 1: Rewrite `generate_gem_preview()` in `gemini_service.py`

**File:** `backend/app/services/gemini_service.py`

**Steps:**
1. Remove the `create_pre_composite()` function
2. Remove the `estimate_pixels_per_mm()` function
3. Remove the `ImageFilter` import (no longer needed)
4. Rewrite `generate_gem_preview()` to accept:
   - `gem_product_image_bytes: bytes` — the gem product photo
   - `target_photo_bytes: bytes` — the customer/model hand photo
   - `prompt: str` — the narrative prompt (includes Pass 1 description)
   - `body_part: str` — for aspect ratio hints
5. Inside the function:
   - Open both images with PIL
   - Detect the target photo's aspect ratio (w/h) and map to nearest Gemini-supported ratio
   - Call `client.models.generate_content()` with:
     - `model="gemini-2.5-flash-image"`
     - `contents=[prompt, gem_product_img, target_img]`
     - `config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"], image_config=types.ImageConfig(aspect_ratio=detected_ratio))`
   - Extract and return the image bytes from `part.inline_data.data`

**Verify:** Function signature is clean, no pre-composite dependencies remain.

### Task 2: Rewrite `build_prompt()` in `try_on.py`

**File:** `backend/app/api/try_on.py`

**Steps:**
1. Rewrite `build_prompt()` to use the narrative multi-image composition template from the Gemini docs
2. The prompt should follow this pattern (adapted from the docs' "Advanced Composition" and "High-fidelity detail preservation" templates):

```
Create a photorealistic jewelry preview photograph.

Image 1 shows a loose gemstone — use it as the visual reference for the gem's exact appearance.
Image 2 shows a person's {body_part} — this is the base photograph to edit.

GEMSTONE IDENTITY (from analysis):
{gem_description}

YOUR TASK:
Take the gemstone from Image 1 and place it in a {style_name} {category} setting made of {metal_desc} on the {placement} of the person in Image 2.

The gemstone is {dim_text} — render it at its correct real-world size relative to the {body_part}. It should appear small and proportional, as real jewelry does on a human {body_part}.

Setting style: {style_desc}.

Ensure the final image looks like a professional jewelry photograph:
- Preserve the person's skin texture, tone, and background exactly as-is
- Match the lighting direction and color temperature from Image 2
- Add realistic {metal} reflections and subtle shadows where the ring meets the skin
- The gemstone must match the color, cut, and brilliance from Image 1 exactly
- Output only the final photograph, no text
```

3. Keep `METAL_DETAILS` and `STYLE_DETAILS` dicts unchanged
4. Keep `_format_gem_description()` unchanged
5. Remove dimension-related "do NOT change" rules — replace with natural size description

**Verify:** Prompt reads as a natural description, not a list of rules.

### Task 3: Update endpoint wiring in `try_on.py`

**File:** `backend/app/api/try_on.py`

**Steps:**
1. Update the `generate_preview()` endpoint to pass the correct args to the new `generate_gem_preview()`:
   - Remove `context_image_bytes` parameter (already done)
   - Pass `gem_product_image_bytes=gem_image_bytes`
   - Pass `target_photo_bytes=target_photo_bytes`
   - Pass `prompt=prompt_text`
   - Pass `body_part=body_part`
   - Remove `gem_length_mm` and `gem_width_mm` params (no longer needed for pre-composite)
2. Keep Pass 1 orchestration unchanged (analyze_gem still uses product + context images)

**Verify:** `python -c "from app.api.try_on import router"` succeeds without import errors.

### Task 4: Add aspect ratio detection utility

**File:** `backend/app/services/gemini_service.py`

**Steps:**
1. Add a helper function `detect_aspect_ratio(img: Image.Image) -> str` that:
   - Calculates w/h ratio
   - Maps to nearest Gemini-supported ratio from: `"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"`
   - Default to `"3:4"` for portrait-ish photos, `"4:3"` for landscape-ish
2. Use this in `generate_gem_preview()` for the `image_config`

**Verify:** Test with a 1080x1920 image → should return "9:16". Test with 4032x3024 → should return "4:3".

### Task 5: Clean up and test

**Steps:**
1. Remove unused imports from `gemini_service.py` (`ImageFilter`)
2. Ensure `analyze_gem()` and `validate_customer_photo()` are untouched
3. Run the backend: `cd backend && python -m uvicorn app.main:app --port 8001`
4. Verify no import errors or startup failures
5. Test end-to-end via the frontend: upload a gem, select settings, use a customer hand photo

**Verify:** Backend starts cleanly, generation endpoint returns a result image.

---

## Files Changed

| File | Change |
|------|--------|
| `backend/app/services/gemini_service.py` | Remove pre-composite pipeline, rewrite generate_gem_preview() |
| `backend/app/api/try_on.py` | Rewrite build_prompt(), update endpoint wiring |

## Files NOT Changed

| File | Reason |
|------|--------|
| Frontend (all files) | API contract unchanged (FormData in, result_url out) |
| `backend/app/api/gems.py` | Unrelated |
| `backend/app/models/schemas.py` | Schema unchanged |
| `backend/app/api/utils.py` | Upload functions unchanged |
| Pass 1 (analyze_gem) | Still valuable — provides text description for prompt |

---

## Rollback Plan

If the multi-image approach produces worse results than pre-composite:
1. The git history preserves the pre-composite code
2. Can revert `gemini_service.py` and `try_on.py` to restore the old approach
3. Alternative: try `gemini-3-pro-image-preview` model which has thinking mode and handles complex compositions better (but may have different pricing/availability)

---

## Key Gemini API Patterns Referenced

1. **Advanced Composition** (dress+model → fashion photo)
2. **High-fidelity detail preservation** (logo+shirt → branded photo)
3. **Inpainting/Semantic masking** (change only X, keep everything else)
4. **Narrative prompting** ("describe the scene, don't just list keywords")
5. **`image_config` with `aspect_ratio`** for matching output dimensions
