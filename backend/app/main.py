from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api import products, hand_models, prompts, try_on
from .config import settings
import os

app = FastAPI(title="retouch-gem API")

# CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3001,http://localhost:8001").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.(ngrok-free\.app|dokploy\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(hand_models.router, prefix="/api/hand-models", tags=["hand-models"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])
app.include_router(try_on.router, prefix="/api/try-on", tags=["try-on"])

@app.get("/")
def read_root():
    return {"message": "Welcome to retouch-gem API"}
