from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.database import get_db
from app.schemas.clothing_item import ClothingItemResponse
from app.services import clothing_service

router = APIRouter(prefix="/clothing-items", tags=["Clothing"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/",
    response_model=ClothingItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_clothing_item(
    db: DBSession,
    current_user: CurrentUser,
    name: Annotated[str, Form()],
    category: Annotated[str, Form()],
    color: Annotated[str, Form()],
    image: Annotated[UploadFile | None, File()] = None,
):
    return await clothing_service.create_clothing_item(
        db, current_user.id, name, category, color, image
    )


@router.get("/", response_model=list[ClothingItemResponse])
async def get_clothing_items(
    db: DBSession,
    current_user: CurrentUser,
):
    return await clothing_service.get_clothing_items(db, current_user.id)


@router.get("/{clothing_id}", response_model=ClothingItemResponse)
async def get_clothing_item(
    clothing_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    return await clothing_service.get_clothing_item(db, current_user.id, clothing_id)


@router.delete("/{clothing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clothing_item(
    clothing_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    await clothing_service.delete_clothing_item(db, current_user.id, clothing_id)


@router.put("/{clothing_id}", response_model=ClothingItemResponse)
async def update_clothing_item(
    clothing_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    name: Annotated[str, Form()],
    category: Annotated[str, Form()],
    color: Annotated[str, Form()],
    image: Annotated[UploadFile | None, File()] = None,
):
    return await clothing_service.update_clothing_item(
        db,
        current_user.id,
        clothing_id,
        name,
        category,
        color,
        image,
    )
