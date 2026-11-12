from uuid import UUID

from pydantic import BaseModel, Field


class OutfitRecommendationRequest(BaseModel):
    occasion: str = Field(min_length=2, max_length=100)
    season: str = Field(min_length=2, max_length=50)
    style: str = Field(default="Any", max_length=50)
    additional_requirements: str | None = Field(
        default=None,
        max_length=500,
    )


class OutfitSuggestion(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    clothing_item_ids: list[UUID] = Field(min_length=2)
    explanation: str = Field(min_length=1)


class OutfitRecommendationResponse(BaseModel):
    suggestions: list[OutfitSuggestion] = Field(
        min_length=1,
        max_length=3,
    )
