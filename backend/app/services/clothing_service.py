from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clothing_item import ClothingItem
from app.utils.files import MEDIA_DIR, delete_image_file


async def _save_image(image: UploadFile) -> str:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed",
        )

    extension = Path(image.filename or "").suffix.lower() or ".jpg"
    filename = f"{uuid4()}{extension}"
    file_path = MEDIA_DIR / filename

    with file_path.open("wb") as buffer:
        while chunk := await image.read(1024 * 1024):
            buffer.write(chunk)

    return f"/media/{filename}"


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
    await db.commit()
    await db.refresh(item)

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

    delete_image_file(image_url)


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

    if image is not None:
        old_image_url = item.image_url
        item.image_url = await _save_image(image)

    await db.commit()
    await db.refresh(item)

    if old_image_url:
        delete_image_file(old_image_url)

    return item
