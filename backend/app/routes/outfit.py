from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.auth import CurrentUser, DBSession
from app.schemas.outfit import OutfitCreate, OutfitResponse, OutfitUpdate
from app.schemas.outfit_recommendation import (
    OutfitRecommendationRequest,
    OutfitRecommendationResponse,
)
from app.services import ai_outfit_service, outfit_service

router = APIRouter(prefix="/outfits", tags=["Outfits"])


@router.post(
    "/",
    response_model=OutfitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_outfit(
    outfit_data: OutfitCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    return await outfit_service.create_outfit(db, current_user.id, outfit_data)


@router.get("/", response_model=list[OutfitResponse])
async def get_outfits(
    current_user: CurrentUser,
    db: DBSession,
):
    return await outfit_service.get_outfits(db, current_user.id)


@router.get("/{outfit_id}", response_model=OutfitResponse)
async def get_outfit(
    outfit_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    return await outfit_service.get_outfit(db, current_user.id, outfit_id)


@router.put("/{outfit_id}", response_model=OutfitResponse)
async def update_outfit(
    outfit_id: UUID,
    current_user: CurrentUser,
    outfit_data: OutfitUpdate,
    db: DBSession,
):
    return await outfit_service.update_outfit(
        db, current_user.id, outfit_id, outfit_data
    )


@router.delete("/{outfit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_outfit(
    outfit_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    await outfit_service.delete_outfit(db, current_user.id, outfit_id)


@router.post(
    "/recommendations",
    response_model=OutfitRecommendationResponse,
)
async def recommend_outfits(
    requirements: OutfitRecommendationRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    try:
        return await ai_outfit_service.generate_recommendations(
            db,
            current_user.id,
            requirements,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc