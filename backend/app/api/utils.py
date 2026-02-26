import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
import os
from supabase import create_client, Client
from ..config import settings

UPLOAD_DIR = Path("uploads")

# Initialize Supabase client
supabase: Client = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    print(f"Initializing Supabase client with URL: {settings.SUPABASE_URL}")
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
else:
    print("WARNING: Supabase URL or Key missing in configuration.")
    print(f"URL present: {bool(settings.SUPABASE_URL)}, Key present: {bool(settings.SUPABASE_KEY)}")

def save_uploaded_file(file: UploadFile, subfolder: str) -> str:
    subfolder_path = UPLOAD_DIR / subfolder
    subfolder_path.mkdir(parents=True, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    if not file_extension:
        file_extension = ".jpg" # Default if none provided
    
    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = subfolder_path / file_name
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return str(file_path)

def get_file_url(file_path: str) -> str:
    # Assuming frontend expects /uploads/subfolder/filename
    path = Path(file_path)
    return f"/api/uploads/{path.relative_to(UPLOAD_DIR)}"

async def upload_to_supabase_storage(file: UploadFile, bucket: str) -> str:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        file_extension = os.path.splitext(file.filename)[1]
        if not file_extension:
            file_extension = ".jpg"
        
        file_name = f"{uuid.uuid4()}{file_extension}"
        file_content = await file.read()
        
        # Reset file pointer for later use if needed (though we already read it)
        await file.seek(0)

        res = supabase.storage.from_(bucket).upload(
            path=file_name,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Get public URL
        url = supabase.storage.from_(bucket).get_public_url(file_name)
        return url
    except Exception as e:
        print(f"Supabase Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def upload_bytes_to_supabase(content: bytes, bucket: str, content_type: str = "image/jpeg") -> str:
    if not supabase:
         # Fallback to local if not configured? No, let's keep it consistent.
         raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        file_name = f"{uuid.uuid4()}.jpg"
        supabase.storage.from_(bucket).upload(
            path=file_name,
            file=content,
            file_options={"content-type": content_type}
        )
        url = supabase.storage.from_(bucket).get_public_url(file_name)
        return url
    except Exception as e:
        print(f"Supabase Bytes Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
