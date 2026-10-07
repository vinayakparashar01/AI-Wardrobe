from uuid import UUID

from app.core.auth import CurrentUser
from app.db.database import get_db
from app.schemas.outfit import OutfitCreate, OutfitResponse, OutfitUpdate
from app.services import outfit_service
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/outfits", tags=["Outfits"])


@router.post(
    "/",
    response_model=OutfitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_outfit(
    outfit_data: OutfitCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    return await outfit_service.create_outfit(
        db, current_user.id, outfit_data
    )


@router.get("/", response_model=list[OutfitResponse])
async def get_outfits(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    return await outfit_service.get_outfits(db, current_user.id)


@router.get("/{outfit_id}", response_model=OutfitResponse)
async def get_outfit(
    outfit_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    return await outfit_service.get_outfit(
        db, current_user.id, outfit_id
    )


@router.put("/{outfit_id}", response_model=OutfitResponse)
async def update_outfit(
    outfit_id: UUID,
    current_user: CurrentUser,
    outfit_data: OutfitUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await outfit_service.update_outfit(
        db, current_user.id, outfit_id, outfit_data
    )


@router.delete("/{outfit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_outfit(
    outfit_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    await outfit_service.delete_outfit(
        db, current_user.id, outfit_id
    )
