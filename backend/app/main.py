from app.routers.auth import router as auth_router
from app.routers.clothing import router as clothing_router
from app.routers.user import router as user_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
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


@app.get("/")
async def home():
    return {"message": "AI Wardrobe is running"}
