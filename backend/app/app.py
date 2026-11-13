from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routes.auth import router as auth_router
from app.routes.clothing import router as clothing_router
from app.routes.outfit import router as outfit_router
from app.routes.user import router as user_router

app = FastAPI(title="AI Wardrobe API")

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/media",
    StaticFiles(directory=MEDIA_DIR),
    name="media",
)

cors_origins = settings.cors_origins
# Per CORS standard: wildcard origin cannot be combined with allow_credentials=True.
# Authentication in AI Wardrobe uses the Authorization Bearer header, not browser cookies.
allow_credentials = cors_origins != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(clothing_router)
app.include_router(outfit_router)


@app.get("/")
async def home():
    return {"message": "AI Wardrobe is running"}
