from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.auth import router as auth_router
from app.routers.clothing import router as clothing_router
from app.routers.outfit import router as outfit_router
from app.routers.user import router as user_router

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_DIR = BASE_DIR / "media"

app.mount(
    "/media",
    StaticFiles(directory=MEDIA_DIR),
    name="media",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clothing_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(outfit_router)


@app.get("/")
async def home():
    return {"message": "AI Wardrobe is running"}
