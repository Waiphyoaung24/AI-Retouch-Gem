from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices
from fastapi import Header, HTTPException, status
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "secret123")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    SUPABASE_URL: str = Field(default="", validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"))
    SUPABASE_KEY: str = Field(default="", validation_alias=AliasChoices(
        "SUPABASE_KEY", 
        "NEXT_PUBLIC_SUPABASE_ANON_KEY", 
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY"
    ))
    UPLOAD_DIR: str = "uploads"
    DATA_DIR: str = "data"
    DEFAULT_PROMPT_ID: str = "default"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

async def verify_admin(x_admin_key: Optional[str] = Header(None)):
    if x_admin_key != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )
