from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class ProductBase(BaseModel):
    name: str

class Product(ProductBase):
    id: str
    image_path: str
    image_url: str
    created_at: str

class HandModelBase(BaseModel):
    name: str

class HandModel(HandModelBase):
    id: str
    image_path: str
    image_url: str

class PromptBase(BaseModel):
    name: str
    body: str

class Prompt(PromptBase):
    id: str
    is_default: bool
    created_at: str

class TryOnRequest(BaseModel):
    product_id: Optional[str] = None
    hand_model_id: str

class TryOnResult(BaseModel):
    result_url: str
    cached: bool
    processing_time_ms: float

class CacheEntry(BaseModel):
    id: str # cache_key
    result_url: str
    created_at: str
