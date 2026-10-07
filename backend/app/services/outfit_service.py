from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clothing_item import ClothingItem
from app.models.outfit import Outfit
from app.models.outfit_item import OutfitItem
from app.schemas.outfit import OutfitCreate, OutfitResponse, OutfitUpdate


async def _validate_clothing_items(
    db: AsyncSession,
    user_id: UUID,
    clothing_item_ids: list[UUID],
) -> None:
    result = await db.execute(
        select(ClothingItem).where(
            ClothingItem.id.in_(clothing_item_ids),
            ClothingItem.user_id == user_id,
        )
    )
    clothing_items = result.scalars().all()

    if len(clothing_items) != len(set(clothing_item_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more clothing items do not belong to you",
        )


async def _get_clothing_item_ids(
    db: AsyncSession,
    outfit_id: UUID,
) -> list[UUID]:
    result = await db.execute(
        select(OutfitItem.clothing_item_id).where(
            OutfitItem.outfit_id == outfit_id
        )
    )
    return list(result.scalars().all())


def _to_response(
    outfit: Outfit,
    clothing_item_ids: list[UUID],
) -> OutfitResponse:
    return OutfitResponse(
        id=outfit.id,
        user_id=outfit.user_id,
        name=outfit.name,
        description=outfit.description,
        is_favorite=outfit.is_favorite,
        clothing_item_ids=clothing_item_ids,
        created_at=outfit.created_at,
        updated_at=outfit.updated_at,
    )


async def create_outfit(
    db: AsyncSession,
    user_id: UUID,
    outfit_data: OutfitCreate,
) -> OutfitResponse:
    await _validate_clothing_items(
        db, user_id, outfit_data.clothing_item_ids
    )

    outfit = Outfit(
        user_id=user_id,
        name=outfit_data.name,
        description=outfit_data.description,
        is_favorite=outfit_data.is_favorite,
    )

    db.add(outfit)
    await db.flush()

    for clothing_item_id in outfit_data.clothing_item_ids:
        db.add(
            OutfitItem(
                outfit_id=outfit.id,
                clothing_item_id=clothing_item_id,
            )
        )

    await db.commit()
    await db.refresh(outfit)

    return _to_response(outfit, outfit_data.clothing_item_ids)


async def get_outfits(
    db: AsyncSession,
    user_id: UUID,
) -> list[OutfitResponse]:
    result = await db.execute(
        select(Outfit)
        .where(Outfit.user_id == user_id)
        .order_by(Outfit.created_at.desc())
    )

    outfits = result.scalars().all()
    responses = []

    for outfit in outfits:
        item_ids = await _get_clothing_item_ids(db, outfit.id)
        responses.append(_to_response(outfit, item_ids))

    return responses


async def get_outfit(
    db: AsyncSession,
    user_id: UUID,
    outfit_id: UUID,
) -> OutfitResponse:
    result = await db.execute(
        select(Outfit).where(
            Outfit.id == outfit_id,
            Outfit.user_id == user_id,
        )
    )
    outfit = result.scalar_one_or_none()

    if outfit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outfit not found",
        )

    item_ids = await _get_clothing_item_ids(db, outfit.id)
    return _to_response(outfit, item_ids)


async def update_outfit(
    db: AsyncSession,
    user_id: UUID,
    outfit_id: UUID,
    outfit_data: OutfitUpdate,
) -> OutfitResponse:
    result = await db.execute(
        select(Outfit).where(
            Outfit.id == outfit_id,
            Outfit.user_id == user_id,
        )
    )
    outfit = result.scalar_one_or_none()

    if outfit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outfit not found",
        )

    if outfit_data.name is not None:
        outfit.name = outfit_data.name
    if outfit_data.description is not None:
        outfit.description = outfit_data.description
    if outfit_data.is_favorite is not None:
        outfit.is_favorite = outfit_data.is_favorite

    if outfit_data.clothing_item_ids is not None:
        await _validate_clothing_items(
            db, user_id, outfit_data.clothing_item_ids
        )

        await db.execute(
            delete(OutfitItem).where(OutfitItem.outfit_id == outfit.id)
        )

        for clothing_item_id in outfit_data.clothing_item_ids:
            db.add(
                OutfitItem(
                    outfit_id=outfit.id,
                    clothing_item_id=clothing_item_id,
                )
            )

    await db.commit()
    await db.refresh(outfit)

    item_ids = await _get_clothing_item_ids(db, outfit.id)
    return _to_response(outfit, item_ids)


async def delete_outfit(
    db: AsyncSession,
    user_id: UUID,
    outfit_id: UUID,
) -> None:
    result = await db.execute(
        select(Outfit).where(
            Outfit.id == outfit_id,
            Outfit.user_id == user_id,
        )
    )
    outfit = result.scalar_one_or_none()

    if outfit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outfit not found",
        )

    await db.delete(outfit)
    await db.commit()
