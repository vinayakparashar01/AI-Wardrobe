from typing import Annotated
from uuid import UUID

from app.core.auth import CurrentUser
from app.db.database import get_db
from app.models.clothing_item import ClothingItem
from app.schemas.clothing_item import ClothingItemCreate, ClothingItemResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/clothing-items", tags=["Clothing"])
DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/",
    response_model=ClothingItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_clothing_item(
    clothing: ClothingItemCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    item = ClothingItem(
        user_id=current_user.id,
        name=clothing.name,
        category=clothing.category,
        color=clothing.color,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return item


@router.get(
    "/",
    response_model=list[ClothingItemResponse],
)
async def get_clothing_items(
    db: DBSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ClothingItem).where(ClothingItem.user_id == current_user.id)
    )

    return result.scalars().all()


@router.get(
    "/{clothing_id}",
    response_model=ClothingItemResponse,
)
async def get_clothing_item(
    clothing_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    item = await db.get(ClothingItem, clothing_id)

    if item is None or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found",
        )

    return item


@router.delete(
    "/{clothing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_clothing_item(
    clothing_id: UUID,
    db: DBSession,
    current_user:CurrentUser,
):
    item = await db.get(ClothingItem, clothing_id)

    if item is None or item.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="clothing item not found",
        )
    await db.delete(item)
    await db.commit()
