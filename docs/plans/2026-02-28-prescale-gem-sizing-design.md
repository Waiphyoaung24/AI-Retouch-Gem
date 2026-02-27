# Pre-Scale Gem Image for Accurate Sizing

**Date:** 2026-02-28
**Status:** Implemented

## Problem

Gemini's image generation model ignores text-based size instructions. The gem-to-finger ratio number in the prompt (whether 20%, 25%, or 33%) has no measurable effect on the generated gem size. The model renders the gem large because the product photo fills its entire frame — Gemini sees a "big" gem and produces a big gem.

## Solution

Pre-scale the gem product image before sending it to Gemini so the gem is visually at the correct proportion relative to the target hand image.

### Pipeline

1. **Upload time** (MediaPipe + Gemini bbox): Measure gem-to-finger ratio from context photo → store in DB as `gem_to_finger_ratio` (e.g. 25.0 meaning 25% of finger width)
2. **Generation time** (pre-scaling):
   - Run MediaPipe on the target hand photo → get ring finger width in pixels
   - Compute target gem size: `finger_width_px * (ratio / 100)`
   - Resize gem product image to that pixel width
   - Center it on a white canvas matching target image dimensions
   - Send this pre-scaled image as Gemini's "element image"

### Key Insight

Gemini respects the visual size of elements in input images. By making the gem physically small in a large canvas, the model renders it small in the output.

## Files Changed

| File | Change |
|------|--------|
| `backend/app/services/gemini_service.py` | Added `_prescale_gem_image()`, updated `generate_gem_preview()` signature |
| `backend/app/services/hand_analysis.py` | Added `measure_gem_to_finger_ratio()` using MediaPipe + Gemini bbox |
| `backend/app/api/try_on.py` | Pass `gem_to_finger_ratio` to `generate_gem_preview()` |
| `backend/app/api/gems.py` | Call `measure_gem_to_finger_ratio()` at upload time |
| `backend/app/models/schemas.py` | Added `gem_to_finger_ratio` field to `Gem` model |
| `backend/migrations/004_gem_to_finger_ratio.sql` | New DB column |
