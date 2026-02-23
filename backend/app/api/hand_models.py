from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List
from ..models.schemas import HandModel, HandModelBase
from ..api.utils import upload_to_supabase_storage, supabase
from ..config import verify_admin
import uuid

router = APIRouter()

@router.get("/", response_model=List[HandModel])
async def list_hand_models():
    if not supabase:
        return []
    
    try:
        response = supabase.table("hand_models").select("*").execute()
        # image_path is optional or empty for Supabase entries
        return [HandModel(**item, image_path="") for item in response.data]
    except Exception as e:
        print(f"Supabase Select Error: {e}")
        return []

@router.post("/", response_model=HandModel)
async def create_hand_model(
    name: str = Form(...),
    image: UploadFile = File(...),
    _ = Depends(verify_admin)
):
    try:
        # 1. Upload to Supabase Storage
        image_url = await upload_to_supabase_storage(image, "hand-models")
        
        # 2. Insert into Supabase DB
        new_id = str(uuid.uuid4())
        data = {
            "id": new_id,
            "name": name,
            "image_url": image_url
        }
        
        supabase.table("hand_models").insert(data).execute()
        
        return HandModel(id=new_id, name=name, image_url=image_url, image_path="")
    except Exception as e:
        print(f"Supabase Create Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{hand_model_id}")
async def delete_hand_model(
    hand_model_id: str,
    _ = Depends(verify_admin)
):
    try:
        # Optional: Delete from storage too if you have the filename
        # For now, just delete from DB
        supabase.table("hand_models").delete().eq("id", hand_model_id).execute()
        return {"message": "Hand model deleted"}
    except Exception as e:
        print(f"Supabase Delete Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
