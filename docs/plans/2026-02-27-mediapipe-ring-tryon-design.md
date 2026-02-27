# MediaPipe Ring Try-On: Hybrid Preview + Gemini Refinement

**Date:** 2026-02-27
**Status:** Approved

## Overview

Add a server-side MediaPipe hand analysis pipeline that produces an instant ring preview (Pillow compositing), while Gemini auto-generates a photorealistic version in the background. Earring and pendant categories are locked ("Coming Soon") — rings only for now.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Approach | Hybrid (canvas preview + auto Gemini) | Fast feedback + photorealistic result |
| Finger selection | Auto ring finger + tap to switch | Best UX — smart default with override |
| Scale calibration | Context image calibration | Zero user effort, uses existing gem-on-hand photo |
| Preview rendering | Composite actual gem product photo | Real gem image, no template assets needed |
| MediaPipe runtime | Server-side Python (mediapipe 0.10.32) | Keeps frontend thin, more Pillow control |
| Wizard step 1 | Keep with locked categories | Builds anticipation for future features |
| Gemini trigger | Auto-fire in background, crossfade | Seamless upgrade, no extra button |

## Architecture

### Data Flow

```
Customer uploads hand photo
        |
        v
POST /api/try-on/preview  (NEW endpoint)
        |
        +-> Run MediaPipe on context_image_url (gem-on-hand)
        |     -> get finger landmarks + pixel width
        |     -> compute scale factor using gem's known mm dimensions
        |
        +-> Run MediaPipe on customer's hand photo
        |     -> get finger landmarks (all 5 fingers)
        |     -> default to ring finger (landmarks 13-14)
        |
        +-> Pillow compositing:
        |     -> draw metallic band arc across finger
        |     -> scale + place gem product_image_url on finger
        |     -> return composited preview image
        |
        +-> Response: { preview_url, fingers, scale_info }

Frontend shows preview immediately
        |
        v
Auto-fires POST /api/try-on/generate  (EXISTING endpoint)
        |
        v
Gemini photorealistic result -> crossfade replaces preview
```

## Scale Calibration System

The gem's `context_image_url` shows the gem held against a hand. We exploit this:

1. Run MediaPipe on `context_image_url` -> get ring finger landmarks (13=MCP, 14=PIP)
2. Measure finger width in pixels at the PIP joint
3. Use Gemini Flash (existing Pass 1) to locate the gem's bounding box in the context image -> gem pixel dimensions
4. **Scale factor** = `gem_length_mm / gem_pixel_length` -> `mm_per_pixel`
5. Apply: `finger_width_px x mm_per_pixel` = real finger width in mm

For the customer's photo:
1. Run MediaPipe -> get ring finger width in pixels
2. `customer_mm_per_pixel = known_finger_width_mm / customer_finger_width_px`
3. Scale gem image: `gem_width_mm / customer_mm_per_pixel` = gem render width in pixels

**Fallback:** If MediaPipe fails on context image, use statistical average (~17mm ring finger width).

## Ring Compositing Pipeline

Server-side Pillow compositing for `POST /api/try-on/preview`:

1. **Detect landmarks** on customer photo. Identify all fingers, default to ring finger.
2. **Calculate placement point.** Ring sits between PIP (landmark 14) and DIP (landmark 15). Midpoint = ring center.
3. **Calculate finger angle.** PIP->DIP angle determines ring rotation.
4. **Size the gem.** Using calibrated `mm_per_pixel`, scale `product_image_url` to real-world dimensions.
5. **Draw the band.** Pillow `ImageDraw` elliptical arc across finger width. Color by metal:
   - Gold: #CA8A04
   - White Gold: #C0C0C0
   - Rose Gold: #B76E79
   - Silver: #AAA9AD
   - Band width: ~15% of finger width
6. **Place the gem.** Paste scaled, rotated gem product image centered above the band. Remove gem background via threshold-based alpha masking.
7. **Alpha blending.** Threshold or grab-cut to isolate gem from its background before pasting.
8. **Return** composited image + landmark coordinates as JSON for finger-switcher UI.

## Frontend UX Changes

### Wizard Modifications

- **Step 1 (Category):** Ring selectable. Earring and Pendant get semi-transparent overlay with lock icon + "Coming Soon". Clicking them does nothing.
- **Steps 2-3 (Metal, Style):** Unchanged.
- **Step 4 (Photo):** Unchanged.

### Result Screen (New Behavior)

1. User clicks "Generate Preview" -> loading spinner.
2. **Preview arrives (~1-2s):** Display Pillow-composited image. Overlay circular tap targets on each detected finger (translucent dots at PIP-DIP midpoint). Active finger has highlighted ring icon. Tapping another finger sends new `POST /api/try-on/preview` with `finger_index` -> replaces preview.
3. **Gemini auto-fires** in background when first preview loads. Thin animated progress bar below image.
4. **Gemini result arrives (~15-30s):** Crossfade animation replaces preview. Finger-tap targets disappear.
5. **Actions:** Download button + Try Another button.

No new pages or routes. Everything within `/gem/[id]`.

## Backend: New Service

### `backend/app/services/hand_analysis.py`

```
hand_analysis.py
+-- analyze_hand(image_bytes) -> HandAnalysis
|     Runs mediapipe.solutions.hands on the image
|     Returns: { landmarks, handedness, image_width, image_height }
|
+-- calibrate_scale(context_image_bytes, gem_length_mm, gem_width_mm) -> ScaleInfo
|     1. analyze_hand() on context image
|     2. Gemini Flash to locate gem bounding box
|     3. Compute mm_per_pixel
|     Returns: { mm_per_pixel, finger_width_mm, gem_bbox }
|
+-- composite_ring_preview(...) -> bytes (PNG)
|     1. analyze_hand() on customer photo
|     2. Calculate gem render size
|     3. Remove gem background (alpha mask)
|     4. Draw metallic band
|     5. Paste scaled gem
|     Returns: composited image bytes
|
+-- get_finger_positions(landmarks, image_w, image_h) -> list[FingerPosition]
      Extracts PIP-DIP midpoint for each finger
      Returns: [{ finger_name, x, y, angle }]
```

### New Endpoint

```
POST /api/try-on/preview
  Form: gem_id, metal_id, model_photo_id OR customer_photo, finger_index (optional, default=14)
  Returns: { preview_url, fingers: [...], scale_info: {...} }
```

## File Changes

### New Files
| File | Purpose |
|------|---------|
| `backend/app/services/hand_analysis.py` | MediaPipe detection, scale calibration, Pillow compositing |

### Modified Files
| File | Changes |
|------|---------|
| `backend/app/api/try_on.py` | Add `POST /api/try-on/preview` endpoint |
| `backend/app/models/schemas.py` | Add `RingPreviewResult`, `FingerPosition`, `ScaleInfo` schemas |
| `backend/pyproject.toml` | Add `mediapipe>=0.10.32` dependency |
| `frontend/src/lib/api.ts` | Add `RingPreviewResult` type + `generateRingPreview()` |
| `frontend/src/app/gem/[id]/page.tsx` | Lock categories, preview->Gemini crossfade, finger tap targets |
| `frontend/src/app/globals.css` | Crossfade animation, locked overlay, finger-dot styles |

### No Changes
- No new pages or routes
- No database migrations
- No new tables

## Execution Order

1. Backend: Add `mediapipe>=0.10.32` dependency
2. Backend: Create `hand_analysis.py` service
3. Backend: Add schemas + `/api/try-on/preview` endpoint
4. Frontend: Lock categories UI
5. Frontend: Add `generateRingPreview()` API call
6. Frontend: Rewrite result screen (preview, auto-fire Gemini, crossfade, finger taps)
7. End-to-end test with real gem + hand photo

## MediaPipe Hand Landmarks Reference

```
 0: WRIST
 1: THUMB_CMC       5: INDEX_MCP       9: MIDDLE_MCP     13: RING_MCP      17: PINKY_MCP
 2: THUMB_MCP       6: INDEX_PIP      10: MIDDLE_PIP     14: RING_PIP      18: PINKY_PIP
 3: THUMB_IP        7: INDEX_DIP      11: MIDDLE_DIP     15: RING_DIP      19: PINKY_DIP
 4: THUMB_TIP       8: INDEX_TIP      12: MIDDLE_TIP     16: RING_TIP      20: PINKY_TIP
```

Ring placement: midpoint of landmarks 14 (RING_PIP) and 15 (RING_DIP).
All coordinates are normalized [0.0, 1.0] relative to image dimensions.
