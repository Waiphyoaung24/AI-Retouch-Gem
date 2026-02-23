# retouch-gem — Design Plan
**Date:** 2026-02-23
**Project:** Jewellery Virtual Try-On with Gemini Image Editing

---

## 1. Project Summary

A web app that lets customers see how a gem or jewellery piece looks on a hand model. Businesses share a link; customers browse or upload jewellery photos, pick a pre-set hand model, and Gemini composites the jewellery onto the hand in a realistic way.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Next.js Frontend                   │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Customer UI  │  │  Admin Panel │  │ Try-On UI │  │
│  │ (browse +    │  │ (products,   │  │ (pick hand │  │
│  │  upload)     │  │  models,     │  │  model +   │  │
│  │              │  │  prompts)    │  │  result)   │  │
│  └──────────────┘  └──────────────┘  └───────────┘  │
└────────────────────────┬────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────┐
│                  FastAPI Backend                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Products   │  │  Hand Models │  │  Prompts   │  │
│  │  Router     │  │  Router      │  │  Router    │  │
│  └─────────────┘  └──────────────┘  └────────────┘  │
│  ┌──────────────────────────────────────────────┐    │
│  │        Gemini Image Edit Service             │    │
│  │  (gemini-2.5-flash-image)                    │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
              │ File Storage (local → S3/R2)
```

---

## 3. User Flows

### Customer Flow
1. Land on the page via shareable link
2. Browse admin product catalog OR upload their own jewellery photo
3. Select a hand model from the gallery
4. Click "Try On" → Gemini processes the image (~5-15s)
5. View the result → download or try another hand model

### Admin Flow
1. Login to `/admin`
2. Upload jewellery products (name + image)
3. Upload hand model photos (name + image)
4. Manage prompt templates (write, edit, set default)
5. View try-on history

### Gemini Processing Flow
```
jewellery_image + hand_model_image + prompt_text
        ↓
  gemini-2.5-flash-image
        ↓
  result_image (saved to storage)
        ↓
  URL returned to frontend
```

---

## 4. Gemini Integration

**Model:** `gemini-2.5-flash-image`
**Source:** [Google AI Docs](https://ai.google.dev/gemini-api/docs/image-generation.md)

```python
# backend/app/services/gemini_service.py
from google import genai
from PIL import Image
import io

client = genai.Client()

async def try_on_jewellery(
    jewellery_image_bytes: bytes,
    hand_model_image_bytes: bytes,
    prompt: str,
) -> bytes:
    jewellery_img = Image.open(io.BytesIO(jewellery_image_bytes))
    hand_img = Image.open(io.BytesIO(hand_model_image_bytes))

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt, jewellery_img, hand_img],
    )

    for part in response.parts:
        if part.inline_data is not None:
            return part.inline_data.data  # image bytes

    raise ValueError("Gemini did not return an image")
```

**Default Prompt Template (admin edits this):**
```
You are a professional jewellery retouching artist.
Place the jewellery from the first image onto the hand
in the second image. Maintain realistic lighting, shadows,
and perspective. The jewellery should look naturally worn.
Do not alter the hand or background.
Output only the final edited hand image.
```

**Caching:**
- Results cached by `product_id + hand_model_id` combo
- Admin can force regenerate
- Avoids repeat API calls for same combination

---

## 5. Frontend Design Direction

**Aesthetic:** Luxury editorial — dark background, warm gold accents, serif display typography
**Inspired by:** High-end jewellery brand lookbooks (Cartier, Tiffany)

| Element | Choice |
|---------|--------|
| Background | Deep charcoal `#0d0d0d` |
| Accent | Warm gold `#c9a84c` |
| Text | Off-white `#f5f0e8` |
| Display font | `Cormorant Garamond` (serif, elegant) |
| Body font | `DM Sans` (clean, readable) |
| Motion | Fade-in staggered reveals, smooth image transitions |
| Layout | Asymmetric grid, generous whitespace, editorial feel |

**Key UI Moments:**
- Full-bleed hero with animated jewellery imagery
- Hand model gallery with hover-reveal name
- Try-On loading state: elegant shimmer/pulse animation
- Result reveal: slow fade-in with subtle scale animation

---

## 6. Project Structure

```
retouch-gem/
├── frontend/                    # Next.js 14+ App Router
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Customer landing + catalog
│   │   │   ├── try-on/page.tsx   # Try-on experience
│   │   │   ├── admin/
│   │   │   │   ├── page.tsx      # Admin dashboard
│   │   │   │   ├── products/
│   │   │   │   ├── hand-models/
│   │   │   │   └── prompts/
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ProductCard.tsx
│   │   │   ├── HandModelGallery.tsx
│   │   │   ├── TryOnPanel.tsx
│   │   │   ├── ResultViewer.tsx
│   │   │   └── ui/               # Shared design system
│   │   └── lib/
│   │       └── api.ts            # API client
│   ├── package.json
│   └── tailwind.config.ts
│
├── backend/                     # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── products.py
│   │   │   ├── hand_models.py
│   │   │   ├── prompts.py
│   │   │   └── try_on.py         # Main try-on endpoint
│   │   ├── services/
│   │   │   └── gemini_service.py
│   │   └── models/
│   │       └── schemas.py        # Pydantic models
│   ├── uploads/                  # Local file storage
│   │   ├── products/
│   │   ├── hand-models/
│   │   └── results/
│   ├── pyproject.toml
│   └── .env.example
│
└── docs/
    └── plans/
        └── 2026-02-23-retouch-gem-design.md
```

---

## 7. API Endpoints

```
Products
  GET    /api/products          → list all products
  POST   /api/products          → upload new product (admin)
  DELETE /api/products/{id}     → delete product (admin)

Hand Models
  GET    /api/hand-models        → list active hand models
  POST   /api/hand-models        → upload hand model (admin)
  DELETE /api/hand-models/{id}   → delete hand model (admin)

Prompts
  GET    /api/prompts            → list prompt templates (admin)
  POST   /api/prompts            → create prompt template (admin)
  PUT    /api/prompts/{id}       → update prompt (admin)
  PUT    /api/prompts/{id}/default → set as default (admin)

Try-On
  POST   /api/try-on             → generate result
    body: { product_id, hand_model_id }
    OR:   { jewellery_image (file), hand_model_id }

Static Files
  GET    /uploads/{path}         → serve uploaded images
```

---

## 8. Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+ |
| AI | Google Gen AI SDK (`google-genai`), `gemini-2.5-flash-image` |
| Image handling | Pillow (PIL) |
| Database | PostgreSQL + SQLAlchemy (future) / JSON file store (MVP) |
| File storage | Local filesystem → Cloudflare R2 / S3 |
| Auth (admin) | Simple JWT or hardcoded admin key (MVP) |
| Deployment | Vercel (frontend) + Railway/Render (backend) |

---

## 9. MVP Scope (Phase 1)

Focus on getting the core try-on loop working end-to-end:

- [ ] FastAPI backend with file upload endpoints
- [ ] Gemini service (`gemini-2.5-flash-image` integration)
- [ ] Admin panel: upload products + hand models
- [ ] Admin panel: prompt template editor (set default)
- [ ] Customer page: browse products + try-on flow
- [ ] Customer upload: upload own jewellery image + try-on
- [ ] Result viewer with download button
- [ ] Elegant luxury frontend design

**Out of scope for MVP:**
- User accounts / authentication for customers
- Try-on history per customer
- S3 migration
- Result sharing / social features

---

## 10. Key Dependencies

```toml
# backend/pyproject.toml
[dependencies]
fastapi = ">=0.115"
uvicorn = ">=0.30"
google-genai = ">=1.0"
Pillow = ">=10.0"
python-multipart = ">=0.0.9"
pydantic = ">=2.0"
python-dotenv = ">=1.0"
aiofiles = ">=23.0"
```

```json
// frontend/package.json (key deps)
{
  "next": "^14.2",
  "react": "^18",
  "typescript": "^5",
  "tailwindcss": "^3.4",
  "axios": "^1.6"
}
```
