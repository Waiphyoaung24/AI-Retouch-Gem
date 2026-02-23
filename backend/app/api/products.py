from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List
from ..models.schemas import Product, ProductBase
from ..api.utils import upload_to_supabase_storage, supabase
from ..config import verify_admin
import uuid
import datetime

router = APIRouter()

@router.get("/", response_model=List[Product])
async def list_products():
    if not supabase:
        return []
    
    try:
        response = supabase.table("products").select("*").execute()
        return [Product(**item, image_path="") for item in response.data]
    except Exception as e:
        print(f"Supabase Select Products Error: {e}")
        return []

@router.post("/", response_model=Product)
async def create_product(
    name: str = Form(...),
    image: UploadFile = File(...),
    _ = Depends(verify_admin)
):
    try:
        # 1. Upload to Supabase Storage
        image_url = await upload_to_supabase_storage(image, "products")
        
        # 2. Insert into Supabase DB
        new_id = str(uuid.uuid4())
        now = str(datetime.datetime.now())
        data = {
            "id": new_id,
            "name": name,
            "image_url": image_url,
            "created_at": now
        }
        
        supabase.table("products").insert(data).execute()
        
        return Product(id=new_id, name=name, image_url=image_url, image_path="", created_at=now)
    except Exception as e:
        print(f"Supabase Create Product Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    _ = Depends(verify_admin)
):
    try:
        supabase.table("products").delete().eq("id", product_id).execute()
        return {"message": "Product deleted"}
    except Exception as e:
        print(f"Supabase Delete Product Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
