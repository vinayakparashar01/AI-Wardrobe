from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OutfitCreate(BaseModel):
    name: str = Field(min_length=1,max_length=100)
    description: str | None = None
    clothing_item_ids: list[UUID] = Field(min_length=1)
    is_favorite: bool = False
    
class OutfitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    clothing_item_ids: list[UUID] | None = Field(default=None, min_length=1)
    is_favorite: bool | None = None


class OutfitResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    is_favorite: bool
    clothing_item_ids: list[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    