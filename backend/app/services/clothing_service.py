import asyncio
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clothing_item import ClothingItem
from app.utils.files import MEDIA_DIR, delete_image_file, upload_image_to_cloudinary


async def _save_image(image: UploadFile) -> str:
    """Upload image to Cloudinary and return its secure URL."""
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed",
        )

    upload_result = await asyncio.to_thread(upload_image_to_cloudinary, image)
    return upload_result.secure_url


async def create_clothing_item(
    db: AsyncSession,
    user_id: UUID,
    name: str,
    category: str,
    color: str,
    image: UploadFile | None = None,
) -> ClothingItem:
    image_url = await _save_image(image) if image else None

    item = ClothingItem(
        user_id=user_id,
        name=name,
        category=category,
        color=color,
        image_url=image_url,
    )

    db.add(item)
    try:
        await db.commit()
        await db.refresh(item)
    except Exception:
        await db.rollback()
        if image_url:
            await asyncio.to_thread(delete_image_file, image_url)
        raise

    return item


async def get_clothing_items(
    db: AsyncSession,
    user_id: UUID,
) -> list[ClothingItem]:
    result = await db.execute(
        select(ClothingItem).where(ClothingItem.user_id == user_id)
    )
    return list(result.scalars().all())


async def get_clothing_item(
    db: AsyncSession,
    user_id: UUID,
    clothing_id: UUID,
) -> ClothingItem:
    item = await db.get(ClothingItem, clothing_id)

    if item is None or item.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clothing item not found",
        )

    return item


async def delete_clothing_item(
    db: AsyncSession,
    user_id: UUID,
    clothing_id: UUID,
) -> None:
    item = await get_clothing_item(db, user_id, clothing_id)
    image_url = item.image_url

    await db.delete(item)
    await db.commit()

    if image_url:
        await asyncio.to_thread(delete_image_file, image_url)


async def update_clothing_item(
    db: AsyncSession,
    user_id: UUID,
    clothing_id: UUID,
    name: str,
    category: str,
    color: str,
    image: UploadFile | None = None,
) -> ClothingItem:
    item = await get_clothing_item(db, user_id, clothing_id)

    item.name = name
    item.category = category
    item.color = color

    old_image_url = None
    new_image_url = None

    if image is not None:
        old_image_url = item.image_url
        new_image_url = await _save_image(image)
        item.image_url = new_image_url

    try:
        await db.commit()
        await db.refresh(item)
    except Exception:
        await db.rollback()
        if new_image_url:
            await asyncio.to_thread(delete_image_file, new_image_url)
        raise

    if old_image_url:
        await asyncio.to_thread(delete_image_file, old_image_url)

    return item
