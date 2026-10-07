from uuid import UUID

from app.core.auth import CurrentUser
from app.db.database import get_db
from app.models.clothing_item import ClothingItem
from app.models.outfit import Outfit
from app.models.outfit_item import OutfitItem
from app.schemas.outfit import OutfitCreate, OutfitResponse, OutfitUpdate
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/outfits",
    tags=["outfits"],
)


@router.post(
    "/",
    response_model=OutfitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_outfits(
    outfit_data: OutfitCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClothingItem).where(
            ClothingItem.id.in_(outfit_data.clothing_item_ids),
            ClothingItem.user_id == current_user.id,
        )
    )
    clothing_items = result.scalars().all()

    if len(clothing_items) != len(set(outfit_data.clothing_item_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more clothing items do not belong to you",
        )

    outfit = Outfit(
        user_id=current_user.id,
        name=outfit_data.name,
        description=outfit_data.description,
        is_favorite=outfit_data.is_favorite,
    )

    db.add(outfit)
    await db.flush()

    for clothing_item_id in outfit_data.clothing_item_ids:
        outfit_item = OutfitItem(
            outfit_id=outfit.id,
            clothing_item_id=clothing_item_id,
        )
        db.add(outfit_item)

    await db.commit()
    await db.refresh(outfit)

    return OutfitResponse(
        id=outfit.id,
        user_id=outfit.user_id,
        name=outfit.name,
        description=outfit.description,
        is_favorite=outfit.is_favorite,
        clothing_item_ids=outfit_data.clothing_item_ids,
        created_at=outfit.created_at,
        updated_at=outfit.updated_at,
    )


@router.get(
    "/",
    response_model=list[OutfitResponse],
)
async def get_outfits(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Outfit)
        .where(Outfit.user_id == current_user.id)
        .order_by(Outfit.created_at.desc())
    )

    outfits = result.scalars().all()

    responses = []

    for outfit in outfits:
        items_result = await db.execute(
            select(OutfitItem.clothing_item_id).where(OutfitItem.outfit_id == outfit.id)
        )

        clothing_item_ids = list(items_result.scalars().all())

        responses.append(
            OutfitResponse(
                id=outfit.id,
                user_id=outfit.user_id,
                name=outfit.name,
                description=outfit.description,
                is_favorite=outfit.is_favorite,
                clothing_item_ids=clothing_item_ids,
                created_at=outfit.created_at,
                updated_at=outfit.updated_at,
            )
        )

    return responses

@router.get(
    "/{outfit_id}",
    response_model=OutfitResponse,
)
async def get_outfit(
    outfit_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Outfit).where(
            Outfit.id == outfit_id,
            Outfit.user_id == current_user.id,
        )
    )

    outfit = result.scalar_one_or_none()

    if outfit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outfit not found",
        )

    items_result = await db.execute(
        select(OutfitItem.clothing_item_id).where(
            OutfitItem.outfit_id == outfit.id
        )
    )

    clothing_item_ids = list(items_result.scalars().all())

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

@router.put(
    "/{outfit_id}",
    response_model=OutfitResponse,
)
async def update_outfit(
    outfit_id: UUID,
    current_user: CurrentUser,
    outfit_data: OutfitUpdate,
    db: AsyncSession= Depends(get_db),
):
    result = await db.execute(
        select(Outfit).where(
            Outfit.id == outfit_id,
            Outfit.user_id == current_user.id,
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
        result = await db.execute(
            select(ClothingItem).where(
                ClothingItem.id.in_(outfit_data.clothing_item_ids),
                ClothingItem.user_id == current_user.id,
            )
        )

        clothing_items = result.scalars().all()

        if len(clothing_items) != len(set(outfit_data.clothing_item_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more clothing items do not belong to you",
            )

        await db.execute(
            delete(OutfitItem).where(
                OutfitItem.outfit_id == outfit.id
            )
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

    items_result = await db.execute(
        select(OutfitItem.clothing_item_id).where(
            OutfitItem.outfit_id == outfit.id
        )
    )

    clothing_item_ids = list(items_result.scalars().all())

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
    
@router.delete(
    "/{outfit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_outfit(
    outfit_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result= await db.execute(
        select(Outfit).where(
            Outfit.id == outfit_id,
            Outfit.user_id == current_user.id,
        )
    )
    
    outfit = result.scalar_one_or_none()
    
    if outfit is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="Outfit not found",   
        )
    
    await db.delete(outfit)
    await db.commit()
