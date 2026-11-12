"""Tests for AI Stylist outfit recommendations and resilience (Task Bundle 1)."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clothing_item import ClothingItem
from app.services import ai_outfit_service


async def _create_clothing_item(db: AsyncSession, user_id, name: str, category: str, color: str) -> ClothingItem:
    item = ClothingItem(
        user_id=user_id,
        name=name,
        category=category,
        color=color,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@pytest.mark.asyncio
async def test_empty_wardrobe_returns_400(async_client: AsyncClient, test_user: dict):
    """User with 0 items gets 400 Bad Request instructing them to add items."""
    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "Casual", "season": "Summer", "style": "Streetwear"},
    )
    assert response.status_code == 400
    assert "Your wardrobe is empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_single_item_wardrobe_returns_400(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
):
    """User with only 1 item gets 400 Bad Request requiring at least 2 items."""
    await _create_clothing_item(db_session, test_user["user"].id, "Blue Jeans", "Lower", "Blue")

    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "Casual", "season": "Summer", "style": "Streetwear"},
    )
    assert response.status_code == 400
    assert "You only have 1 clothing item" in response.json()["detail"]


@pytest.mark.asyncio
async def test_two_items_wardrobe_returns_one_suggestion(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """User with 2 items gets max 1 suggestion with mocked Gemini."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "White Tee", "Upper", "White")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Black Jeans", "Lower", "Black")

    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "suggestions": [
            {
                "name": "Classic Monochrome",
                "clothing_item_ids": [str(item1.id), str(item2.id)],
                "explanation": "A clean, timeless white tee and black jeans pairing.",
            }
        ]
    })

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(ai_outfit_service.genai, "Client", lambda *args, **kwargs: mock_client)

    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "Casual", "season": "Summer", "style": "Minimalist"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["name"] == "Classic Monochrome"
    assert set(data["suggestions"][0]["clothing_item_ids"]) == {str(item1.id), str(item2.id)}


@pytest.mark.asyncio
async def test_three_items_wardrobe_returns_up_to_two_suggestions(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """User with 3 items gets up to 2 distinct suggestions."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "White Tee", "Upper", "White")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Black Jeans", "Lower", "Black")
    item3 = await _create_clothing_item(db_session, test_user["user"].id, "Denim Jacket", "Upper", "Blue")

    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "suggestions": [
            {
                "name": "Look 1",
                "clothing_item_ids": [str(item1.id), str(item2.id)],
                "explanation": "Tee and jeans.",
            },
            {
                "name": "Look 2",
                "clothing_item_ids": [str(item2.id), str(item3.id)],
                "explanation": "Jacket and jeans.",
            },
            {
                "name": "Look 3 (Extra)",
                "clothing_item_ids": [str(item1.id), str(item2.id), str(item3.id)],
                "explanation": "Layered look.",
            },
        ]
    })

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(ai_outfit_service.genai, "Client", lambda *args, **kwargs: mock_client)

    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "College", "season": "Winter", "style": "Casual"},
    )

    assert response.status_code == 200
    data = response.json()
    # 3 items caps at max 2 suggestions
    assert len(data["suggestions"]) == 2


@pytest.mark.asyncio
async def test_four_items_wardrobe_returns_up_to_three_suggestions(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """User with 4+ items can receive up to 3 suggestions."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "White Tee", "Upper", "White")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Black Jeans", "Lower", "Black")
    item3 = await _create_clothing_item(db_session, test_user["user"].id, "Sneakers", "Shoes", "White")
    item4 = await _create_clothing_item(db_session, test_user["user"].id, "Leather Watch", "Accessories", "Brown")

    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "suggestions": [
            {
                "name": "Full Ensemble",
                "clothing_item_ids": [str(item1.id), str(item2.id), str(item3.id), str(item4.id)],
                "explanation": "Complete head-to-toe look.",
            },
            {
                "name": "Casual Duo",
                "clothing_item_ids": [str(item1.id), str(item2.id)],
                "explanation": "Simple clean base.",
            },
            {
                "name": "Street Pair",
                "clothing_item_ids": [str(item2.id), str(item3.id)],
                "explanation": "Bottom focus.",
            },
        ]
    })

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(ai_outfit_service.genai, "Client", lambda *args, **kwargs: mock_client)

    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "Casual", "season": "Spring", "style": "Streetwear"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["suggestions"]) == 3


@pytest.mark.asyncio
async def test_gemini_api_timeout_returns_503(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Gemini API timeout triggers clean HTTP 503 Service Unavailable."""
    await _create_clothing_item(db_session, test_user["user"].id, "Item 1", "Upper", "Black")
    await _create_clothing_item(db_session, test_user["user"].id, "Item 2", "Lower", "Blue")

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(side_effect=asyncio.TimeoutError())
    monkeypatch.setattr(ai_outfit_service.genai, "Client", lambda *args, **kwargs: mock_client)

    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "Party", "season": "Summer", "style": "Chic"},
    )

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_gemini_api_exception_returns_503(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Gemini API exception triggers clean HTTP 503 Service Unavailable."""
    await _create_clothing_item(db_session, test_user["user"].id, "Item 1", "Upper", "Black")
    await _create_clothing_item(db_session, test_user["user"].id, "Item 2", "Lower", "Blue")

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("API connection refused"))
    monkeypatch.setattr(ai_outfit_service.genai, "Client", lambda *args, **kwargs: mock_client)

    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "Party", "season": "Summer", "style": "Chic"},
    )

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_gemini_unparseable_json_returns_502(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Gemini returning invalid JSON returns HTTP 502 Bad Gateway."""
    await _create_clothing_item(db_session, test_user["user"].id, "Item 1", "Upper", "Black")
    await _create_clothing_item(db_session, test_user["user"].id, "Item 2", "Lower", "Blue")

    mock_response = MagicMock()
    mock_response.text = "This is not valid JSON at all: {{bad_data}"

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(ai_outfit_service.genai, "Client", lambda *args, **kwargs: mock_client)

    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "Party", "season": "Summer", "style": "Chic"},
    )

    assert response.status_code == 502
    assert "invalid response" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_gemini_invented_ids_filtered_out(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Gemini returning non-existent IDs results in dropping invalid outfits."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "Item 1", "Upper", "Black")
    await _create_clothing_item(db_session, test_user["user"].id, "Item 2", "Lower", "Blue")

    # Suggestion contains one real ID and one completely made up UUID
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "suggestions": [
            {
                "name": "Invalid Combo",
                "clothing_item_ids": [str(item1.id), str(uuid4())],
                "explanation": "Invented item in combo.",
            }
        ]
    })

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(ai_outfit_service.genai, "Client", lambda *args, **kwargs: mock_client)

    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "Casual", "season": "Summer", "style": "Casual"},
    )

    # All suggestions were invalid, returns 502
    assert response.status_code == 502
    assert "could not generate valid outfits" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_gemini_duplicate_outfits_deduplicated(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Gemini returning duplicate combinations is deduplicated so user gets distinct looks."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "Item 1", "Upper", "Black")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Item 2", "Lower", "Blue")
    await _create_clothing_item(db_session, test_user["user"].id, "Item 3", "Shoes", "White")

    # Two outfits have the same combination [item1, item2], just different order
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "suggestions": [
            {
                "name": "Outfit A",
                "clothing_item_ids": [str(item1.id), str(item2.id)],
                "explanation": "Look A",
            },
            {
                "name": "Outfit B (Duplicate combo)",
                "clothing_item_ids": [str(item2.id), str(item1.id)],
                "explanation": "Look B same items",
            },
        ]
    })

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(ai_outfit_service.genai, "Client", lambda *args, **kwargs: mock_client)

    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "Casual", "season": "Summer", "style": "Casual"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["name"] == "Outfit A"


@pytest.mark.asyncio
async def test_ai_stylist_wardrobe_user_isolation(
    async_client: AsyncClient,
    test_user: dict,
    second_user: dict,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Ensure user 1 cannot have user 2's clothes suggested in their prompt."""
    user1_item1 = await _create_clothing_item(db_session, test_user["user"].id, "U1 Top", "Upper", "Red")
    user1_item2 = await _create_clothing_item(db_session, test_user["user"].id, "U1 Pant", "Lower", "Blue")

    # User 2 has distinct clothes
    await _create_clothing_item(db_session, second_user["user"].id, "U2 Top", "Upper", "Green")
    await _create_clothing_item(db_session, second_user["user"].id, "U2 Pant", "Lower", "Yellow")

    captured_prompt = None

    async def mock_generate_content(*args, **kwargs):
        nonlocal captured_prompt
        captured_prompt = kwargs.get("contents")
        res = MagicMock()
        res.text = json.dumps({
            "suggestions": [
                {
                    "name": "User 1 Look",
                    "clothing_item_ids": [str(user1_item1.id), str(user1_item2.id)],
                    "explanation": "Isolated user look",
                }
            ]
        })
        return res

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = mock_generate_content
    monkeypatch.setattr(ai_outfit_service.genai, "Client", lambda *args, **kwargs: mock_client)

    response = await async_client.post(
        "/outfits/recommendations",
        headers=test_user["headers"],
        json={"occasion": "Casual", "season": "Summer", "style": "Casual"},
    )

    assert response.status_code == 200
    assert captured_prompt is not None
    # User 1's items must be in the prompt
    assert str(user1_item1.id) in captured_prompt
    assert str(user1_item2.id) in captured_prompt
    # User 2's items must NOT be in the prompt
    assert "U2 Top" not in captured_prompt
    assert "U2 Pant" not in captured_prompt
