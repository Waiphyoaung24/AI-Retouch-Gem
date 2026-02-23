from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from ..models.schemas import TryOnResult, TryOnRequest, Product, HandModel, Prompt, CacheEntry
from ..services.gemini_service import try_on_jewellery
from ..api.utils import upload_bytes_to_supabase, supabase
import uuid
import datetime
import time
import httpx

router = APIRouter()

DEFAULT_PROMPT = """You are a professional jewellery retouching artist.
Place the jewellery from the first image onto the hand
in the second image. Maintain realistic lighting, shadows,
and perspective. The jewellery should look naturally worn.
Do not alter the hand or background.
Output only the final edited hand image."""

async def fetch_image_bytes(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to fetch image from {url}")
        return response.content

@router.post("/", response_model=TryOnResult)
async def try_on(
    product_id: Optional[str] = Form(None),
    hand_model_id: str = Form(...),
    jewellery_image: Optional[UploadFile] = File(None)
):
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Supabase not configured")

        # 1. Get Hand Model from Supabase
        hm_res = supabase.table("hand_models").select("*").eq("id", hand_model_id).single().execute()
        if not hm_res.data:
            raise HTTPException(status_code=404, detail="Hand model not found")
        
        hand_model_url = hm_res.data["image_url"]
        hand_model_bytes = await fetch_image_bytes(hand_model_url)

        # 2. Get Jewellery Image
        jewellery_bytes = None
        cache_key = None
        start_time = time.time()

        if product_id:
            # Catalog product from Supabase
            p_res = supabase.table("products").select("*").eq("id", product_id).single().execute()
            if not p_res.data:
                raise HTTPException(status_code=404, detail="Product not found")
            
            product_url = p_res.data["image_url"]
            jewellery_bytes = await fetch_image_bytes(product_url)
            
            # Cache check (Optional: could also move results_cache to Supabase)
            cache_key = f"{product_id}:{hand_model_id}"
        elif jewellery_image:
            # Custom upload
            jewellery_bytes = await jewellery_image.read()
        else:
            raise HTTPException(status_code=400, detail="Either product_id or jewellery_image must be provided")

        # 3. Call Gemini
        # (Assuming prompts logic remains local or you want to migrate it later)
        prompt_text = DEFAULT_PROMPT 

        result_bytes = await try_on_jewellery(
            jewellery_image_bytes=jewellery_bytes,
            hand_model_image_bytes=hand_model_bytes,
            prompt=prompt_text
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # 4. Save Result to Supabase Storage
        result_url = await upload_bytes_to_supabase(result_bytes, "results")
        
        return TryOnResult(
            result_url=result_url,
            cached=False,
            processing_time_ms=processing_time
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
