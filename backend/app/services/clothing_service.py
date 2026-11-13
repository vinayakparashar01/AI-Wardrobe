import asyncio
import os
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clothing_item import ClothingItem
from app.utils.files import MEDIA_DIR, delete_image_file, upload_image_to_cloudinary

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def validate_image_file(image: UploadFile) -> None:
    content_type = (image.content_type or "").lower().strip()

    # Reject non-image mime types (preserves existing 400 contract)
    if not content_type or not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed",
        )

    # Reject unsupported image mime types
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image format. Allowed formats are JPEG, PNG, and WebP.",
        )

    # Reject unsupported filename extensions if filename is present
    if image.filename:
        ext = Path(image.filename).suffix.lower()
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file extension '{ext}'. Allowed formats are JPEG, PNG, and WebP.",
            )

    # Validate file size
    file_obj = getattr(image, "file", image)
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)

    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty.",
        )

    if size > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File size exceeds the 5 MB limit.",
        )

    # Validate binary signature / magic bytes
    header = file_obj.read(16)
    file_obj.seek(0)

    is_jpeg = header.startswith(b"\xff\xd8\xff")
    is_png = header.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP"

    if not (is_jpeg or is_png or is_webp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image content. File signature does not match JPEG, PNG, or WebP.",
        )


async def _save_image(image: UploadFile) -> str:
    """Validate and upload image to Cloudinary and return its secure URL."""
    validate_image_file(image)
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
    remove_image: bool = False,
) -> ClothingItem:
    item = await get_clothing_item(db, user_id, clothing_id)

    item.name = name
    item.category = category
    item.color = color

    old_image_to_delete = None
    new_image_url = None

    if image is not None:
        # Case C — Replace existing image (prioritized even if remove_image is true)
        old_image_to_delete = item.image_url
        new_image_url = await _save_image(image)
        item.image_url = new_image_url
    elif remove_image:
        # Case B — Remove existing image
        old_image_to_delete = item.image_url
        item.image_url = None
    # Case A — Keep existing image: image is None and remove_image is False, item.image_url preserved

    try:
        await db.commit()
        await db.refresh(item)
    except Exception:
        await db.rollback()
        if new_image_url:
            await asyncio.to_thread(delete_image_file, new_image_url)
        raise

    if old_image_to_delete:
        await asyncio.to_thread(delete_image_file, old_image_to_delete)

    return item
