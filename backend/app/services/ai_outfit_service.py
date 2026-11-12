import asyncio
import json
import logging
from uuid import UUID

from fastapi import HTTPException, status
from google import genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.clothing_item import ClothingItem
from app.schemas.outfit_recommendation import (
    OutfitRecommendationRequest,
    OutfitRecommendationResponse,
)

logger = logging.getLogger(__name__)


async def generate_recommendations(
    db: AsyncSession,
    user_id: UUID,
    requirements: OutfitRecommendationRequest,
) -> OutfitRecommendationResponse:
    result = await db.execute(
        select(ClothingItem).where(ClothingItem.user_id == user_id)
    )
    clothes = list(result.scalars().all())

    # Wardrobe size validations
    if len(clothes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your wardrobe is empty. Please add clothing items to your wardrobe first.",
        )

    if len(clothes) == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You only have 1 clothing item. Please add at least one more piece to create complete outfits.",
        )

    # Determine maximum realistic distinct combinations based on wardrobe size
    if len(clothes) == 2:
        max_suggestions = 1
    elif len(clothes) == 3:
        max_suggestions = 2
    else:
        max_suggestions = 3

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

Recommend up to {max_suggestions} distinct outfit(s) (minimum 1, maximum {max_suggestions}) using ONLY the clothing
items listed in the user's wardrobe.

User requirements:
- Occasion: {requirements.occasion}
- Season: {requirements.season}
- Preferred style: {requirements.style}
- Additional requirements: {requirements.additional_requirements or "None"}

Wardrobe:
{json.dumps(wardrobe)}

Rules:
1. Use only the exact clothing IDs provided in the wardrobe.
2. Never invent clothing items or IDs.
3. Each outfit must contain at least two clothing items.
4. If multiple outfits are suggested, each outfit must be meaningfully different and not have identical clothing items.
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

    if not settings.gemini_api_key or settings.gemini_api_key.startswith("your-"):
        logger.error("Gemini API key is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI stylist service is currently unavailable. Please try again shortly.",
        )

    client = genai.Client(api_key=settings.gemini_api_key)

    response = None
    for attempt in range(2):
        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": OutfitRecommendationResponse,
                    },
                ),
                timeout=25.0,
            )
            if response and response.text:
                break
        except asyncio.TimeoutError:
            logger.warning("Gemini API request timed out on attempt %d", attempt + 1)
            if attempt < 1:
                await asyncio.sleep(1.0)
        except Exception as exc:
            logger.warning("Gemini API error on attempt %d: %s", attempt + 1, exc)
            if attempt < 1:
                await asyncio.sleep(1.0)

    if not response or not response.text:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI stylist service is currently unavailable. Please try again shortly.",
        )

    try:
        recommendations = OutfitRecommendationResponse.model_validate_json(
            response.text
        )
    except Exception as exc:
        logger.error("Failed to parse Gemini output: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI stylist returned an invalid response. Please try again.",
        ) from exc

    allowed_ids = {item.id for item in clothes}
    valid_suggestions = []
    seen_combinations = set()

    for suggestion in recommendations.suggestions:
        # Each outfit must have at least two items
        if len(suggestion.clothing_item_ids) < 2:
            continue

        # No duplicate items within an outfit
        if len(set(suggestion.clothing_item_ids)) != len(suggestion.clothing_item_ids):
            continue

        # All items must belong to the user's wardrobe
        if not set(suggestion.clothing_item_ids).issubset(allowed_ids):
            continue

        # No duplicate outfits across suggestions
        outfit_combo = frozenset(suggestion.clothing_item_ids)
        if outfit_combo in seen_combinations:
            continue

        seen_combinations.add(outfit_combo)
        valid_suggestions.append(suggestion)

        if len(valid_suggestions) >= max_suggestions:
            break

    if not valid_suggestions:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI stylist could not generate valid outfits with the current wardrobe pieces. Please try again.",
        )

    return OutfitRecommendationResponse(suggestions=valid_suggestions)
