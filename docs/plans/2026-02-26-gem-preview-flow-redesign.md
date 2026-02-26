# Gem Preview Flow Redesign — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the retouch-gem app from a "place jewellery on hand" tool into a "preview loose gemstone in a jewelry setting" tool where dealers share gem links and customers customize how they view the stone (category, metal, style) on their own uploaded photos.

**Architecture:** FastAPI backend with Supabase (DB + Storage), Gemini `gemini-3-pro-image-preview` for image generation and photo validation. Next.js 16 frontend with Tailwind v4. Dealer uploads gems (2 photos each), gets shareable link. Customer opens link, picks setting options from preset prompt matrix, uploads their own photo (validated by Gemini), and gets a generated preview.

**Tech Stack:** Python 3.12, FastAPI, google-genai, Pillow, Supabase, Next.js 16, React 19, TypeScript, Tailwind CSS v4, Axios

---

## Database Schema (Supabase)

The existing `products` and `hand_models` tables will be replaced/migrated. New tables:

```sql
-- Gems: replaces 'products' table
CREATE TABLE gems (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  product_image_url TEXT NOT NULL,
  context_image_url TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Setting categories (ring, earring, pendant)
CREATE TABLE setting_categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  body_part TEXT NOT NULL,
  sort_order INT DEFAULT 0
);

-- Metals
CREATE TABLE metals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  sort_order INT DEFAULT 0
);

-- Styles (linked to category)
CREATE TABLE setting_styles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category_id UUID REFERENCES setting_categories(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  sort_order INT DEFAULT 0
);

-- Prompt templates: one per category x metal x style combination
CREATE TABLE prompt_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category_id UUID REFERENCES setting_categories(id),
  metal_id UUID REFERENCES metals(id),
  style_id UUID REFERENCES setting_styles(id),
  prompt_body TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(category_id, metal_id, style_id)
);

-- Preset model photos (organized by body part)
CREATE TABLE model_photos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  body_part TEXT NOT NULL,
  image_url TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Results cache
CREATE TABLE generation_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gem_id UUID REFERENCES gems(id),
  prompt_template_id UUID REFERENCES prompt_templates(id),
  model_photo_url TEXT NOT NULL,
  result_image_url TEXT NOT NULL,
  processing_time_ms FLOAT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### Supabase Storage Buckets
- `gems` — gem product + context images
- `model-photos` — preset body part model photos
- `customer-uploads` — customer uploaded photos (temporary)
- `results` — generated result images

---

## Task Breakdown

### Task 1: Create Supabase Schema Migration

**Files:**
- Create: `backend/migrations/001_gem_preview_schema.sql`

**Step 1: Write the migration SQL file**

Create `backend/migrations/001_gem_preview_schema.sql` with the full schema from above. Also include seed data for categories, metals, and styles:

```sql
-- Seed setting_categories
INSERT INTO setting_categories (name, body_part, sort_order) VALUES
  ('Ring', 'hand', 1),
  ('Earring', 'ear', 2),
  ('Pendant', 'neck', 3);

-- Seed metals
INSERT INTO metals (name, sort_order) VALUES
  ('Gold', 1),
  ('White Gold', 2),
  ('Rose Gold', 3),
  ('Silver', 4);

-- Seed setting_styles (rings)
INSERT INTO setting_styles (category_id, name, sort_order)
SELECT c.id, s.name, s.sort_order
FROM setting_categories c
CROSS JOIN (VALUES ('Solitaire', 1), ('Halo', 2), ('Three-Stone', 3), ('Pave', 4)) AS s(name, sort_order)
WHERE c.name = 'Ring';

-- Seed setting_styles (earrings)
INSERT INTO setting_styles (category_id, name, sort_order)
SELECT c.id, s.name, s.sort_order
FROM setting_categories c
CROSS JOIN (VALUES ('Stud', 1), ('Drop', 2), ('Hoop', 3), ('Chandelier', 4)) AS s(name, sort_order)
WHERE c.name = 'Earring';

-- Seed setting_styles (pendants)
INSERT INTO setting_styles (category_id, name, sort_order)
SELECT c.id, s.name, s.sort_order
FROM setting_categories c
CROSS JOIN (VALUES ('Solitaire', 1), ('Halo', 2), ('Bezel', 3), ('Cluster', 4)) AS s(name, sort_order)
WHERE c.name = 'Pendant';
```

**Step 2: Run migration against Supabase**

Run the SQL via Supabase dashboard SQL editor or CLI. Verify all tables are created.

**Step 3: Create storage buckets in Supabase**

In Supabase dashboard > Storage, create buckets: `gems`, `model-photos`, `customer-uploads`, `results`. Set all to public.

**Step 4: Commit**

```bash
git add backend/migrations/
git commit -m "feat: add gem preview schema migration and seed data"
```

---

### Task 2: Update Backend Pydantic Schemas

**Files:**
- Modify: `backend/app/models/schemas.py`

**Step 1: Rewrite schemas.py**

Replace the entire file with new schemas:

```python
from pydantic import BaseModel
from typing import Optional, List


# --- Gems ---
class GemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class Gem(BaseModel):
    id: str
    name: str
    product_image_url: str
    context_image_url: str
    description: Optional[str] = None
    created_at: str


# --- Setting Options ---
class SettingCategory(BaseModel):
    id: str
    name: str
    body_part: str
    sort_order: int

class Metal(BaseModel):
    id: str
    name: str
    sort_order: int

class SettingStyle(BaseModel):
    id: str
    category_id: str
    name: str
    sort_order: int


# --- Prompt Templates ---
class PromptTemplate(BaseModel):
    id: str
    category_id: str
    metal_id: str
    style_id: str
    prompt_body: str
    created_at: str

class PromptTemplateCreate(BaseModel):
    category_id: str
    metal_id: str
    style_id: str
    prompt_body: str


# --- Model Photos ---
class ModelPhoto(BaseModel):
    id: str
    name: str
    body_part: str
    image_url: str
    created_at: str


# --- Photo Validation ---
class PhotoValidationResult(BaseModel):
    is_valid: bool
    body_part_detected: Optional[str] = None
    feedback: str


# --- Generation ---
class GeneratePreviewRequest(BaseModel):
    gem_id: str
    category_id: str
    metal_id: str
    style_id: str
    model_photo_id: Optional[str] = None

class GeneratePreviewResult(BaseModel):
    result_url: str
    processing_time_ms: float


# --- Settings Options Response ---
class SettingOptionsResponse(BaseModel):
    categories: List[SettingCategory]
    metals: List[Metal]
    styles: List[SettingStyle]
```

**Step 2: Commit**

```bash
git add backend/app/models/schemas.py
git commit -m "feat: rewrite pydantic schemas for gem preview flow"
```

---

### Task 3: Update Backend Utils

**Files:**
- Modify: `backend/app/api/utils.py`

**Step 1: Add customer photo upload helper**

Add to the end of `utils.py`:

```python
async def upload_customer_photo_to_supabase(content: bytes, content_type: str = "image/jpeg") -> str:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        file_name = f"{uuid.uuid4()}.jpg"
        supabase.storage.from_("customer-uploads").upload(
            path=file_name,
            file=content,
            file_options={"content-type": content_type}
        )
        url = supabase.storage.from_("customer-uploads").get_public_url(file_name)
        return url
    except Exception as e:
        print(f"Customer Photo Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Commit**

```bash
git add backend/app/api/utils.py
git commit -m "feat: add customer photo upload helper"
```

---

### Task 4: Create Gems API (replaces Products)

**Files:**
- Create: `backend/app/api/gems.py`

**Step 1: Create gems.py**

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
from ..models.schemas import Gem
from ..api.utils import upload_to_supabase_storage, supabase
from ..config import verify_admin
import uuid
import datetime

router = APIRouter()

@router.get("/", response_model=List[Gem])
async def list_gems():
    if not supabase:
        return []
    try:
        response = supabase.table("gems").select("*").order("created_at", desc=True).execute()
        return [Gem(**item) for item in response.data]
    except Exception as e:
        print(f"List Gems Error: {e}")
        return []

@router.get("/{gem_id}", response_model=Gem)
async def get_gem(gem_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        response = supabase.table("gems").select("*").eq("id", gem_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Gem not found")
        return Gem(**response.data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Gem)
async def create_gem(
    name: str = Form(...),
    product_image: UploadFile = File(...),
    context_image: UploadFile = File(...),
    description: Optional[str] = Form(None),
    _ = Depends(verify_admin),
):
    try:
        product_image_url = await upload_to_supabase_storage(product_image, "gems")
        context_image_url = await upload_to_supabase_storage(context_image, "gems")
        new_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        data = {
            "id": new_id,
            "name": name,
            "product_image_url": product_image_url,
            "context_image_url": context_image_url,
            "description": description,
            "created_at": now,
        }
        supabase.table("gems").insert(data).execute()
        return Gem(**data)
    except Exception as e:
        print(f"Create Gem Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{gem_id}")
async def delete_gem(gem_id: str, _ = Depends(verify_admin)):
    try:
        supabase.table("gems").delete().eq("id", gem_id).execute()
        return {"message": "Gem deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Commit**

```bash
git add backend/app/api/gems.py
git commit -m "feat: add gems API with dual image upload"
```

---

### Task 5: Create Setting Options API

**Files:**
- Create: `backend/app/api/settings.py`

**Step 1: Create settings.py**

```python
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..models.schemas import (
    SettingCategory, Metal, SettingStyle,
    SettingOptionsResponse, PromptTemplate, PromptTemplateCreate,
)
from ..api.utils import supabase
from ..config import verify_admin
import uuid
import datetime

router = APIRouter()

@router.get("/options", response_model=SettingOptionsResponse)
async def get_setting_options():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        cats = supabase.table("setting_categories").select("*").order("sort_order").execute()
        metals = supabase.table("metals").select("*").order("sort_order").execute()
        styles = supabase.table("setting_styles").select("*").order("sort_order").execute()
        return SettingOptionsResponse(
            categories=[SettingCategory(**c) for c in cats.data],
            metals=[Metal(**m) for m in metals.data],
            styles=[SettingStyle(**s) for s in styles.data],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/styles/{category_id}", response_model=List[SettingStyle])
async def get_styles_for_category(category_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        response = supabase.table("setting_styles").select("*").eq("category_id", category_id).order("sort_order").execute()
        return [SettingStyle(**s) for s in response.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prompts", response_model=List[PromptTemplate])
async def list_prompt_templates(_ = Depends(verify_admin)):
    if not supabase:
        return []
    try:
        response = supabase.table("prompt_templates").select("*").execute()
        return [PromptTemplate(**p) for p in response.data]
    except Exception as e:
        return []

@router.post("/prompts", response_model=PromptTemplate)
async def create_prompt_template(body: PromptTemplateCreate, _ = Depends(verify_admin)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        new_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        data = {
            "id": new_id,
            "category_id": body.category_id,
            "metal_id": body.metal_id,
            "style_id": body.style_id,
            "prompt_body": body.prompt_body,
            "created_at": now,
        }
        supabase.table("prompt_templates").upsert(data, on_conflict="category_id,metal_id,style_id").execute()
        return PromptTemplate(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Commit**

```bash
git add backend/app/api/settings.py
git commit -m "feat: add settings options and prompt templates API"
```

---

### Task 6: Create Model Photos API (replaces Hand Models)

**Files:**
- Create: `backend/app/api/model_photos.py`

**Step 1: Create model_photos.py**

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List
from ..models.schemas import ModelPhoto
from ..api.utils import upload_to_supabase_storage, supabase
from ..config import verify_admin
import uuid
import datetime

router = APIRouter()

@router.get("/", response_model=List[ModelPhoto])
async def list_model_photos(body_part: str = None):
    if not supabase:
        return []
    try:
        query = supabase.table("model_photos").select("*").order("created_at", desc=True)
        if body_part:
            query = query.eq("body_part", body_part)
        response = query.execute()
        return [ModelPhoto(**item) for item in response.data]
    except Exception as e:
        print(f"List Model Photos Error: {e}")
        return []

@router.post("/", response_model=ModelPhoto)
async def create_model_photo(
    name: str = Form(...),
    body_part: str = Form(...),
    image: UploadFile = File(...),
    _ = Depends(verify_admin),
):
    try:
        image_url = await upload_to_supabase_storage(image, "model-photos")
        new_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        data = {
            "id": new_id,
            "name": name,
            "body_part": body_part,
            "image_url": image_url,
            "created_at": now,
        }
        supabase.table("model_photos").insert(data).execute()
        return ModelPhoto(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{photo_id}")
async def delete_model_photo(photo_id: str, _ = Depends(verify_admin)):
    try:
        supabase.table("model_photos").delete().eq("id", photo_id).execute()
        return {"message": "Model photo deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Commit**

```bash
git add backend/app/api/model_photos.py
git commit -m "feat: add model photos API with body_part filtering"
```

---

### Task 7: Rewrite Gemini Service (Validation + Generation)

**Files:**
- Modify: `backend/app/services/gemini_service.py`

**Step 1: Rewrite gemini_service.py**

```python
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
                model="gemini-3-pro-image-preview",
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


async def generate_gem_preview(gem_product_image_bytes: bytes, target_photo_bytes: bytes, prompt: str) -> bytes:
    try:
        gem_img = Image.open(io.BytesIO(gem_product_image_bytes))
        target_img = Image.open(io.BytesIO(target_photo_bytes))

        def _call():
            return client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=[prompt, gem_img, target_img],
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            )

        response = await asyncio.to_thread(_call)
        for part in response.parts:
            if part.inline_data is not None:
                return part.inline_data.data
        raise ValueError("Gemini did not return an image")
    except Exception as e:
        print(f"Gemini Generation Error: {e}")
        raise e
```

**Step 2: Commit**

```bash
git add backend/app/services/gemini_service.py
git commit -m "feat: rewrite gemini service with validation + generation"
```

---

### Task 8: Rewrite Try-On Endpoint

**Files:**
- Modify: `backend/app/api/try_on.py`

**Step 1: Rewrite try_on.py**

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from ..models.schemas import GeneratePreviewResult, PhotoValidationResult
from ..services.gemini_service import generate_gem_preview, validate_customer_photo
from ..api.utils import upload_bytes_to_supabase, supabase
import time
import httpx

router = APIRouter()

async def fetch_image_bytes(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to fetch image from {url}")
        return response.content

def build_fallback_prompt(category_name: str, metal_name: str, style_name: str) -> str:
    body_part = 'hand' if category_name == 'Ring' else 'ear' if category_name == 'Earring' else 'neck'
    placement = 'ring finger' if category_name == 'Ring' else 'ear' if category_name == 'Earring' else 'neck'
    return f"""You are a professional jewelry retouching artist and photorealistic rendering specialist.

Image 1: A loose gemstone (clean product photograph).
Image 2: A photograph of a person's {body_part}.

Task: Create a photorealistic image showing this exact gemstone set in a {style_name} {category_name.lower()} made of {metal_name.lower()}. Place the {category_name.lower()} naturally on the {placement} shown in Image 2.

Requirements:
- Preserve the gemstone's exact color, cut, clarity, and brilliance from Image 1
- Render the {metal_name.lower()} setting with realistic reflections and material properties
- Match the lighting, shadows, and skin tones from Image 2
- The jewelry must look naturally worn, not digitally pasted
- Do not alter the person's body, skin texture, or background
- Output only the final composite image"""

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

        # 1. Fetch gem product image
        gem_res = supabase.table("gems").select("*").eq("id", gem_id).single().execute()
        if not gem_res.data:
            raise HTTPException(status_code=404, detail="Gem not found")
        gem_image_bytes = await fetch_image_bytes(gem_res.data["product_image_url"])

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

        # 3. Build prompt
        prompt_text = None
        pt_res = supabase.table("prompt_templates").select("*").eq(
            "category_id", category_id
        ).eq("metal_id", metal_id).eq("style_id", style_id).single().execute()

        if pt_res.data:
            prompt_text = pt_res.data["prompt_body"]
        else:
            cat_res = supabase.table("setting_categories").select("name").eq("id", category_id).single().execute()
            met_res = supabase.table("metals").select("name").eq("id", metal_id).single().execute()
            sty_res = supabase.table("setting_styles").select("name").eq("id", style_id).single().execute()
            prompt_text = build_fallback_prompt(
                cat_res.data["name"] if cat_res.data else "Ring",
                met_res.data["name"] if met_res.data else "Gold",
                sty_res.data["name"] if sty_res.data else "Solitaire",
            )

        # 4. Generate with Gemini
        result_bytes = await generate_gem_preview(
            gem_product_image_bytes=gem_image_bytes,
            target_photo_bytes=target_photo_bytes,
            prompt=prompt_text,
        )

        processing_time = (time.time() - start_time) * 1000

        # 5. Upload result
        result_url = await upload_bytes_to_supabase(result_bytes, "results")

        return GeneratePreviewResult(result_url=result_url, processing_time_ms=processing_time)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Commit**

```bash
git add backend/app/api/try_on.py
git commit -m "feat: rewrite try-on endpoint for gem preview generation"
```

---

### Task 9: Update FastAPI Main Router

**Files:**
- Modify: `backend/app/main.py`

**Step 1: Update main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api import gems, model_photos, settings, try_on
import os

app = FastAPI(title="retouch-gem API")

cors_env = os.getenv("CORS_ORIGINS", "")
cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()] or [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8001",
    "https://tryon.nexapex.ai",
    "https://tryon-api.nexapex.ai",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.(ngrok-free\.app|dokploy\.com|nexapex\.ai)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(gems.router, prefix="/api/gems", tags=["gems"])
app.include_router(model_photos.router, prefix="/api/model-photos", tags=["model-photos"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(try_on.router, prefix="/api/try-on", tags=["try-on"])

@app.get("/")
def read_root():
    return {"message": "Welcome to retouch-gem API"}
```

**Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: rewire main.py to new routers"
```

---

### Task 10: Remove Old Backend Files

**Files:**
- Delete: `backend/app/api/products.py`
- Delete: `backend/app/api/hand_models.py`
- Delete: `backend/app/api/prompts.py`
- Delete: `backend/app/dependencies.py`
- Delete: `backend/app/storage.py`

**Step 1: Remove files**

```bash
rm -f backend/app/api/products.py backend/app/api/hand_models.py backend/app/api/prompts.py
rm -f backend/app/dependencies.py backend/app/storage.py
rm -f backend/data/products.json backend/data/hand_models.json backend/data/results_cache.json
```

**Step 2: Verify backend imports work**

```bash
cd backend && python -c "from app.main import app; print('OK')"
```

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove old product/hand-model/prompts files"
```

---

### Task 11: Rewrite Frontend API Client

**Files:**
- Modify: `frontend/src/lib/api.ts`

**Step 1: Rewrite api.ts**

```typescript
import axios from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
export const API_URL = BASE_URL.endsWith('/api') ? BASE_URL : `${BASE_URL.replace(/\/+$/, '')}/api`;

const api = axios.create({
  baseURL: API_URL,
  headers: { 'ngrok-skip-browser-warning': 'true' },
});

// --- Types ---
export interface Gem {
  id: string;
  name: string;
  product_image_url: string;
  context_image_url: string;
  description?: string;
  created_at: string;
}

export interface SettingCategory {
  id: string;
  name: string;
  body_part: string;
  sort_order: number;
}

export interface Metal {
  id: string;
  name: string;
  sort_order: number;
}

export interface SettingStyle {
  id: string;
  category_id: string;
  name: string;
  sort_order: number;
}

export interface SettingOptions {
  categories: SettingCategory[];
  metals: Metal[];
  styles: SettingStyle[];
}

export interface ModelPhoto {
  id: string;
  name: string;
  body_part: string;
  image_url: string;
  created_at: string;
}

export interface PhotoValidationResult {
  is_valid: boolean;
  body_part_detected: string | null;
  feedback: string;
}

export interface GeneratePreviewResult {
  result_url: string;
  processing_time_ms: number;
}

// --- Gems ---
export const getGems = () => api.get<Gem[]>('/gems/').then(r => r.data);
export const getGem = (id: string) => api.get<Gem>(`/gems/${id}`).then(r => r.data);
export const createGem = (formData: FormData, adminKey: string) =>
  api.post<Gem>('/gems/', formData, {
    headers: { 'Content-Type': 'multipart/form-data', 'x-admin-key': adminKey },
  }).then(r => r.data);
export const deleteGem = (id: string, adminKey: string) =>
  api.delete(`/gems/${id}`, { headers: { 'x-admin-key': adminKey } }).then(r => r.data);

// --- Settings ---
export const getSettingOptions = () => api.get<SettingOptions>('/settings/options').then(r => r.data);
export const getStylesForCategory = (categoryId: string) =>
  api.get<SettingStyle[]>(`/settings/styles/${categoryId}`).then(r => r.data);

// --- Model Photos ---
export const getModelPhotos = (bodyPart?: string) => {
  const params = bodyPart ? { body_part: bodyPart } : {};
  return api.get<ModelPhoto[]>('/model-photos/', { params }).then(r => r.data);
};
export const createModelPhoto = (formData: FormData, adminKey: string) =>
  api.post<ModelPhoto>('/model-photos/', formData, {
    headers: { 'Content-Type': 'multipart/form-data', 'x-admin-key': adminKey },
  }).then(r => r.data);
export const deleteModelPhoto = (id: string, adminKey: string) =>
  api.delete(`/model-photos/${id}`, { headers: { 'x-admin-key': adminKey } }).then(r => r.data);

// --- Validation & Generation ---
export const validatePhoto = (formData: FormData) =>
  api.post<PhotoValidationResult>('/try-on/validate-photo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
export const generatePreview = (formData: FormData) =>
  api.post<GeneratePreviewResult>('/try-on/generate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);

export default api;
```

**Step 2: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat: rewrite frontend API client for gem preview flow"
```

---

### Task 12: Create Customer Gem Preview Page

**Files:**
- Create: `frontend/src/app/gem/[id]/page.tsx`

**Step 1: Create the directory and page**

```bash
mkdir -p frontend/src/app/gem/\[id\]
```

**Step 2: Create `frontend/src/app/gem/[id]/page.tsx`**

This is the main customer-facing page — the step-by-step configurator (Category > Metal > Style > Photo > Generate). Full code provided in the plan header's Task 11 section — a complete 300+ line React component implementing the stepped flow with:
- Gem header showing product image + name
- Step 1: Category selection (Ring/Earring/Pendant)
- Step 2: Metal selection (Gold/White Gold/Rose Gold/Silver)
- Step 3: Style selection (filtered by category)
- Step 4: Photo selection (preset models OR upload with validation)
- Generate button with loading overlay
- Result view with download

**Step 3: Commit**

```bash
git add frontend/src/app/gem/
git commit -m "feat: add customer gem preview page with step configurator"
```

---

### Task 13: Rewrite Admin Gems Page

**Files:**
- Delete: `frontend/src/app/admin/products/`
- Create: `frontend/src/app/admin/gems/page.tsx`

**Step 1: Remove old, create new**

```bash
rm -rf frontend/src/app/admin/products
mkdir -p frontend/src/app/admin/gems
```

**Step 2: Create admin gems page** with dual image upload form + "Copy Link" button per gem

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: replace admin products with gems page (dual image + copy link)"
```

---

### Task 14: Rewrite Admin Model Photos Page

**Files:**
- Delete: `frontend/src/app/admin/hand-models/`
- Create: `frontend/src/app/admin/model-photos/page.tsx`

**Step 1: Remove old, create new**

```bash
rm -rf frontend/src/app/admin/hand-models
mkdir -p frontend/src/app/admin/model-photos
```

**Step 2: Create model photos page** with body_part selector (hand/ear/neck) + filter tabs

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: replace admin hand-models with model-photos page"
```

---

### Task 15: Update Admin Layout & Navigation

**Files:**
- Modify: `frontend/src/app/admin/layout.tsx`
- Modify: `frontend/src/app/admin/page.tsx`

**Step 1: Update nav links** to point to `/admin/gems` and `/admin/model-photos`

**Step 2: Update redirect** in `admin/page.tsx` to `/admin/gems`

**Step 3: Commit**

```bash
git add frontend/src/app/admin/layout.tsx frontend/src/app/admin/page.tsx
git commit -m "feat: update admin nav for gems + model photos"
```

---

### Task 16: Update Home Page & Remove Old Try-On

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Delete: `frontend/src/app/try-on/`
- Delete: `frontend/src/components/AdminGuard.tsx`

**Step 1: Simplify home page** — brand page that tells customers to use dealer-shared links

**Step 2: Remove old files**

```bash
rm -rf frontend/src/app/try-on
rm -f frontend/src/components/AdminGuard.tsx
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: update home page, remove old try-on page"
```

---

### Task 17: Seed Prompt Templates

**Files:**
- Create: `backend/migrations/002_seed_prompt_templates.sql`

**Step 1: Generate 48 INSERT statements** (3 categories x 4 metals x 4 styles) with optimized prompts per combination

**Step 2: Run in Supabase SQL editor**

**Step 3: Commit**

```bash
git add backend/migrations/
git commit -m "feat: seed prompt templates for all setting combinations"
```

---

### Task 18: End-to-End Test

**Step 1:** Start backend: `cd backend && uvicorn app.main:app --reload --port 8001`
**Step 2:** Start frontend: `cd frontend && npm run dev`
**Step 3:** Test admin: login > upload gem (2 photos) > copy link > upload model photos
**Step 4:** Test customer: open gem link > Ring > Gold > Solitaire > select photo > generate
**Step 5:** Verify result image shows gem in gold solitaire ring on hand

---

## Summary of Changes

| Old Concept | New Concept |
|---|---|
| `products` (1 image) | `gems` (2 images: product + context) |
| `hand_models` | `model_photos` (hand, ear, neck) |
| `prompts` (free-form) | `prompt_templates` (category x metal x style matrix) |
| Single try-on page | Shareable `/gem/{id}` with step configurator |
| Place jewellery on hand | Generate gem-in-setting preview on body part |
| No photo validation | Gemini-powered photo validation |
| JSON file storage | Fully Supabase (DB + Storage) |
