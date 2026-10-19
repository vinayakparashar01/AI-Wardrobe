import asyncio
import json
from uuid import UUID

from google import genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.clothing_item import ClothingItem
from app.schemas.outfit_recommendation import (
    OutfitRecommendationRequest,
    OutfitRecommendationResponse,
)


async def generate_recommendations(
    db: AsyncSession,
    user_id: UUID,
    requirements: OutfitRecommendationRequest,
) -> OutfitRecommendationResponse:

    result = await db.execute(
        select(ClothingItem).where(
            ClothingItem.user_id == user_id
        )
    )
    clothes = result.scalars().all()

    if len(clothes) < 2:
        raise ValueError(
            "Add more clothes to your wardrobe before generating outfits."
        )

    wardrobe = [
        {
            "id": str(item.id),
            "name": item.name,
            "category": item.category,
            "color": item.color,
        }
        for item in clothes
    ]

    prompt = f"""
You are an expert personal stylist.

Recommend exactly 3 distinct outfits using ONLY the clothing
items listed in the user's wardrobe.

User requirements:
- Occasion: {requirements.occasion}
- Season: {requirements.season}
- Preferred style: {requirements.style}
- Additional requirements: {requirements.additional_requirements or "None"}

Wardrobe:
{json.dumps(wardrobe)}

Rules:
1. Use only the exact clothing IDs provided.
2. Never invent clothing items or IDs.
3. Each outfit must contain at least two clothing items.
4. Make the three outfits meaningfully different.
5. Explain briefly why each outfit suits the requirements.
6. Return JSON matching this structure:
{{
  "suggestions": [
    {{
      "name": "Outfit name",
      "clothing_item_ids": ["existing-UUID"],
      "explanation": "Reason for the recommendation"
    }}
  ]
}}
"""

    client = genai.Client(api_key=settings.gemini_api_key)

    response = None
    last_err = None
    for attempt in range(3):
        try:
            response = await client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": OutfitRecommendationResponse,
                },
            )
            if response and response.text:
                break
        except Exception as exc:
            last_err = exc
            if attempt < 2:
                await asyncio.sleep(1.2 * (attempt + 1))
            else:
                raise ValueError(f"AI service temporarily unavailable: {exc}") from exc

    if not response or not response.text:
        raise ValueError("The AI returned an empty response.")

    recommendations = OutfitRecommendationResponse.model_validate_json(
        response.text
    )

    allowed_ids = {item.id for item in clothes}

    for suggestion in recommendations.suggestions:
        if len(suggestion.clothing_item_ids) < 2:
            raise ValueError("An outfit must contain at least two items.")

        if len(set(suggestion.clothing_item_ids)) != len(
            suggestion.clothing_item_ids
        ):
            raise ValueError("An outfit contains duplicate clothing items.")

        if not set(suggestion.clothing_item_ids).issubset(allowed_ids):
            raise ValueError(
                "The AI returned clothing that isn't in this user's wardrobe."
            )

    return recommendations