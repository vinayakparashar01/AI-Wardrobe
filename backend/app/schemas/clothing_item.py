from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClothingItemCreate(BaseModel):
        name: str
        category: str
        color: str


class ClothingItemResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    category: str
    color: str
    image_url: str | None

    model_config = ConfigDict(from_attributes=True)