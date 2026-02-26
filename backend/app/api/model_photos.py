from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
from ..models.schemas import ModelPhoto
from ..api.utils import upload_to_supabase_storage, supabase
from ..config import verify_admin
import uuid
import datetime

router = APIRouter()

@router.get("/", response_model=List[ModelPhoto])
async def list_model_photos(body_part: Optional[str] = None):
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
