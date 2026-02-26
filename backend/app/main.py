from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api import gems, model_photos, settings, try_on
import os

app = FastAPI(title="retouch-gem API")

cors_env = os.getenv("CORS_ORIGINS", "")
cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()] or [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8001",
    "https://tryon.nexapex.ai",
    "https://tryon-api.nexapex.ai",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.(ngrok-free\.app|dokploy\.com|nexapex\.ai)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(gems.router, prefix="/api/gems", tags=["gems"])
app.include_router(model_photos.router, prefix="/api/model-photos", tags=["model-photos"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(try_on.router, prefix="/api/try-on", tags=["try-on"])

@app.get("/")
def read_root():
    return {"message": "Welcome to retouch-gem API"}
