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
    carat_weight: Optional[float] = Form(None),
    length_mm: Optional[float] = Form(None),
    width_mm: Optional[float] = Form(None),
    depth_mm: Optional[float] = Form(None),
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
            "carat_weight": carat_weight,
            "length_mm": length_mm,
            "width_mm": width_mm,
            "depth_mm": depth_mm,
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
        # Delete related generation_results first (FK constraint)
        supabase.table("generation_results").delete().eq("gem_id", gem_id).execute()
        supabase.table("gems").delete().eq("id", gem_id).execute()
        return {"message": "Gem deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
