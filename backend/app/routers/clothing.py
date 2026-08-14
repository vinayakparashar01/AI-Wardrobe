from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from app.core.auth import CurrentUser
from app.db.database import get_db
from app.models.clothing_item import ClothingItem
from app.schemas.clothing_item import ClothingItemResponse, ClothingItemCreate
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/clothing-items",
    tags=["Clothing"],
)

DBSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


MEDIA_DIR = Path("media")

MEDIA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


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
    image_url = None

    if image is not None:
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed",
            )

        extension = Path(image.filename or "").suffix.lower()

        filename = f"{uuid4()}{extension}"

        file_path = MEDIA_DIR / filename

        with file_path.open("wb") as buffer:
            while chunk := await image.read(1024 * 1024):
                buffer.write(chunk)

        image_url = f"/media/{filename}"

    item = ClothingItem(
        user_id=current_user.id,
        name=name,
        category=category,
        color=color,
        image_url=image_url,
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
    item = await db.get(
        ClothingItem,
        clothing_id,
    )

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
    current_user: CurrentUser,
):
    item = await db.get(
        ClothingItem,
        clothing_id,
    )

    if item is None or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found",
        )

    await db.delete(item)

    await db.commit()
    
@router.put(
    "/{clothing_id}",
    response_model=ClothingItemResponse,
)
async def update_clothing_item(
    clothing_id: UUID,
    clothing: ClothingItemCreate,
    db:DBSession,
    current_user:CurrentUser,
):
    item = await db.get(ClothingItem, clothing_id)
    
    if item is None or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found"
        )
    item.name= clothing.name
    item.category=clothing.category
    item.color=clothing.color
    
    await db.commit()
    await db.refresh(item)
    
    return item
    
