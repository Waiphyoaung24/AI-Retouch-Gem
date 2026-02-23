from fastapi import APIRouter, HTTPException
from typing import List
from ..models.schemas import Prompt
from ..dependencies import prompts_storage
import uuid
import datetime

router = APIRouter()

@router.get("/", response_model=List[Prompt])
async def list_prompts():
    return prompts_storage.get_all()

@router.post("/", response_model=Prompt)
async def create_prompt(
    name: str,
    body: str,
    is_default: bool = False
):
    prompt = Prompt(
        id=str(uuid.uuid4()),
        name=name,
        body=body,
        is_default=is_default,
        created_at=str(datetime.datetime.now())
    )
    prompts_storage.add(prompt)
    if is_default:
        # Unset other defaults
        for p in prompts_storage.get_all():
            if p.id != prompt.id and p.is_default:
                p.is_default = False
                prompts_storage.add(p)
    return prompt

@router.put("/{prompt_id}/default", response_model=Prompt)
async def set_default_prompt(prompt_id: str):
    prompt = prompts_storage.get(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    prompt.is_default = True
    prompts_storage.add(prompt)
    
    for p in prompts_storage.get_all():
        if p.id != prompt_id and p.is_default:
            p.is_default = False
            prompts_storage.add(p)
            
    return prompt
