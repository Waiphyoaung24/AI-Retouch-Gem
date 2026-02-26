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
