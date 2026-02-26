from pydantic import BaseModel
from typing import Optional, List


# --- Gems ---
class GemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    carat_weight: Optional[float] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    depth_mm: Optional[float] = None

class Gem(BaseModel):
    id: str
    name: str
    product_image_url: str
    context_image_url: str
    description: Optional[str] = None
    carat_weight: Optional[float] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    depth_mm: Optional[float] = None
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
