"""Tests for Outfit CRUD, editing, deletion cascades, and completeness (Task Bundle 2)."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clothing_item import ClothingItem


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
async def test_update_outfit_details(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
):
    """Updating outfit name, description, and favorite status preserves items."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "White Tee", "Upper", "White")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Blue Jeans", "Lower", "Blue")

    create_res = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "Summer Casual",
            "description": "Original description",
            "clothing_item_ids": [str(item1.id), str(item2.id)],
            "is_favorite": False,
        },
    )
    assert create_res.status_code == 201
    outfit_id = create_res.json()["id"]

    # Update only metadata
    update_res = await async_client.put(
        f"/outfits/{outfit_id}",
        headers=test_user["headers"],
        json={
            "name": "Winter Chic",
            "description": "Updated description",
            "is_favorite": True,
        },
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["name"] == "Winter Chic"
    assert data["description"] == "Updated description"
    assert data["is_favorite"] is True
    # Items remained untouched
    assert set(data["clothing_item_ids"]) == {str(item1.id), str(item2.id)}
    assert data["is_complete"] is True


@pytest.mark.asyncio
async def test_add_clothing_item_to_outfit(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
):
    """Adding a third clothing piece to an existing 2-piece outfit."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "White Tee", "Upper", "White")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Blue Jeans", "Lower", "Blue")
    item3 = await _create_clothing_item(db_session, test_user["user"].id, "Sneakers", "Shoes", "White")

    create_res = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "Duo Look",
            "clothing_item_ids": [str(item1.id), str(item2.id)],
        },
    )
    assert create_res.status_code == 201
    outfit_id = create_res.json()["id"]

    # Add item3
    update_res = await async_client.put(
        f"/outfits/{outfit_id}",
        headers=test_user["headers"],
        json={
            "clothing_item_ids": [str(item1.id), str(item2.id), str(item3.id)],
        },
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert len(data["clothing_item_ids"]) == 3
    assert set(data["clothing_item_ids"]) == {str(item1.id), str(item2.id), str(item3.id)}
    assert data["is_complete"] is True


@pytest.mark.asyncio
async def test_remove_clothing_item_from_outfit(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
):
    """Removing a piece from an outfit updates associations cleanly."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "White Tee", "Upper", "White")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Blue Jeans", "Lower", "Blue")
    item3 = await _create_clothing_item(db_session, test_user["user"].id, "Sneakers", "Shoes", "White")

    create_res = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "Trio Look",
            "clothing_item_ids": [str(item1.id), str(item2.id), str(item3.id)],
        },
    )
    assert create_res.status_code == 201
    outfit_id = create_res.json()["id"]

    # Remove item2, keeping item1 and item3
    update_res = await async_client.put(
        f"/outfits/{outfit_id}",
        headers=test_user["headers"],
        json={
            "clothing_item_ids": [str(item1.id), str(item3.id)],
        },
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert len(data["clothing_item_ids"]) == 2
    assert str(item2.id) not in data["clothing_item_ids"]
    assert set(data["clothing_item_ids"]) == {str(item1.id), str(item3.id)}
    assert data["is_complete"] is True


@pytest.mark.asyncio
async def test_prevent_duplicate_clothing_references_in_outfit(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
):
    """Duplicate clothing IDs in create or update are rejected with 400 Bad Request."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "White Tee", "Upper", "White")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Blue Jeans", "Lower", "Blue")

    # Creating with duplicates
    res1 = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "Duplicate Create",
            "clothing_item_ids": [str(item1.id), str(item1.id)],
        },
    )
    assert res1.status_code == 400
    assert "Duplicate clothing items" in res1.json()["detail"]

    # Create valid outfit
    create_res = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "Valid Outfit",
            "clothing_item_ids": [str(item1.id), str(item2.id)],
        },
    )
    outfit_id = create_res.json()["id"]

    # Updating with duplicates
    res2 = await async_client.put(
        f"/outfits/{outfit_id}",
        headers=test_user["headers"],
        json={
            "clothing_item_ids": [str(item1.id), str(item2.id), str(item1.id)],
        },
    )
    assert res2.status_code == 400
    assert "Duplicate clothing items" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_reject_clothing_ids_belonging_to_another_user(
    async_client: AsyncClient,
    test_user: dict,
    second_user: dict,
    db_session: AsyncSession,
):
    """User cannot add clothing belonging to another user to their outfit."""
    user1_item = await _create_clothing_item(db_session, test_user["user"].id, "User1 Item", "Upper", "Black")
    user2_item = await _create_clothing_item(db_session, second_user["user"].id, "User2 Item", "Lower", "Red")

    # Creating with another user's item
    res1 = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "Theft Attempt",
            "clothing_item_ids": [str(user1_item.id), str(user2_item.id)],
        },
    )
    assert res1.status_code == 400
    assert "do not belong to you" in res1.json()["detail"]

    # Valid outfit for user 1
    user1_item2 = await _create_clothing_item(db_session, test_user["user"].id, "User1 Item 2", "Lower", "Blue")
    create_res = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "User 1 Outfit",
            "clothing_item_ids": [str(user1_item.id), str(user1_item2.id)],
        },
    )
    outfit_id = create_res.json()["id"]

    # Updating with another user's item
    res2 = await async_client.put(
        f"/outfits/{outfit_id}",
        headers=test_user["headers"],
        json={
            "clothing_item_ids": [str(user1_item.id), str(user2_item.id)],
        },
    )
    assert res2.status_code == 400
    assert "do not belong to you" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_delete_clothing_item_safely_removes_reference_from_outfit(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
):
    """Deleting a clothing item removes its link in outfit_items without deleting the outfit."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "Tee", "Upper", "White")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Jeans", "Lower", "Blue")
    item3 = await _create_clothing_item(db_session, test_user["user"].id, "Cap", "Accessories", "Red")

    create_res = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "Complete Outfit",
            "description": "Great combination",
            "clothing_item_ids": [str(item1.id), str(item2.id), str(item3.id)],
        },
    )
    outfit_id = create_res.json()["id"]

    # Delete item2
    del_res = await async_client.delete(
        f"/clothing-items/{item2.id}",
        headers=test_user["headers"],
    )
    assert del_res.status_code == 204

    # Fetch outfit: outfit exists, item2 is gone, items 1 and 3 remain
    get_res = await async_client.get(
        f"/outfits/{outfit_id}",
        headers=test_user["headers"],
    )
    assert get_res.status_code == 200
    data = get_res.json()
    assert str(item2.id) not in data["clothing_item_ids"]
    assert set(data["clothing_item_ids"]) == {str(item1.id), str(item3.id)}
    assert data["is_complete"] is True


@pytest.mark.asyncio
async def test_preserve_outfit_metadata_after_clothing_deletion(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
):
    """Outfit metadata (name, description, favorite) is preserved even when pieces are deleted."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "Tee", "Upper", "White")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Jeans", "Lower", "Blue")

    create_res = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "Vacation Memory Look",
            "description": "Memories from Italy trip",
            "is_favorite": True,
            "clothing_item_ids": [str(item1.id), str(item2.id)],
        },
    )
    outfit_id = create_res.json()["id"]

    # Delete item1
    await async_client.delete(
        f"/clothing-items/{item1.id}",
        headers=test_user["headers"],
    )

    # Check outfit
    get_res = await async_client.get(
        f"/outfits/{outfit_id}",
        headers=test_user["headers"],
    )
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["name"] == "Vacation Memory Look"
    assert data["description"] == "Memories from Italy trip"
    assert data["is_favorite"] is True


@pytest.mark.asyncio
async def test_handle_incomplete_outfit_when_items_deleted_and_restore(
    async_client: AsyncClient,
    test_user: dict,
    db_session: AsyncSession,
):
    """Outfit drops below 2 pieces is marked is_complete=False and can be restored by adding pieces."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "Tee", "Upper", "White")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "Jeans", "Lower", "Blue")

    create_res = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "Dynamic Look",
            "clothing_item_ids": [str(item1.id), str(item2.id)],
        },
    )
    outfit_id = create_res.json()["id"]
    assert create_res.json()["is_complete"] is True

    # Delete item1 -> only 1 item remaining
    await async_client.delete(
        f"/clothing-items/{item1.id}",
        headers=test_user["headers"],
    )

    res1 = await async_client.get(
        f"/outfits/{outfit_id}",
        headers=test_user["headers"],
    )
    assert res1.status_code == 200
    assert len(res1.json()["clothing_item_ids"]) == 1
    assert res1.json()["is_complete"] is False

    # Delete item2 -> 0 items remaining, outfit still preserved
    await async_client.delete(
        f"/clothing-items/{item2.id}",
        headers=test_user["headers"],
    )

    res2 = await async_client.get(
        f"/outfits/{outfit_id}",
        headers=test_user["headers"],
    )
    assert res2.status_code == 200
    assert len(res2.json()["clothing_item_ids"]) == 0
    assert res2.json()["is_complete"] is False

    # Restore the incomplete outfit by editing and adding new pieces
    new_itemA = await _create_clothing_item(db_session, test_user["user"].id, "New Shirt", "Upper", "Green")
    new_itemB = await _create_clothing_item(db_session, test_user["user"].id, "New Chinos", "Lower", "Khaki")

    update_res = await async_client.put(
        f"/outfits/{outfit_id}",
        headers=test_user["headers"],
        json={
            "clothing_item_ids": [str(new_itemA.id), str(new_itemB.id)],
        },
    )
    assert update_res.status_code == 200
    assert len(update_res.json()["clothing_item_ids"]) == 2
    assert update_res.json()["is_complete"] is True


@pytest.mark.asyncio
async def test_cross_user_outfit_isolation(
    async_client: AsyncClient,
    test_user: dict,
    second_user: dict,
    db_session: AsyncSession,
):
    """User 2 cannot view, edit, or delete User 1's outfit."""
    item1 = await _create_clothing_item(db_session, test_user["user"].id, "U1 Top", "Upper", "Black")
    item2 = await _create_clothing_item(db_session, test_user["user"].id, "U1 Bottom", "Lower", "Black")

    create_res = await async_client.post(
        "/outfits/",
        headers=test_user["headers"],
        json={
            "name": "User 1 Private Outfit",
            "clothing_item_ids": [str(item1.id), str(item2.id)],
        },
    )
    outfit_id = create_res.json()["id"]

    # User 2 attempts to get User 1's outfit
    res_get = await async_client.get(
        f"/outfits/{outfit_id}",
        headers=second_user["headers"],
    )
    assert res_get.status_code == 404

    # User 2 attempts to update User 1's outfit
    res_put = await async_client.put(
        f"/outfits/{outfit_id}",
        headers=second_user["headers"],
        json={"name": "Hacked Outfit"},
    )
    assert res_put.status_code == 404

    # User 2 attempts to delete User 1's outfit
    res_del = await async_client.delete(
        f"/outfits/{outfit_id}",
        headers=second_user["headers"],
    )
    assert res_del.status_code == 404

    # User 2's list does not contain User 1's outfit
    list_res = await async_client.get(
        "/outfits/",
        headers=second_user["headers"],
    )
    assert list_res.status_code == 200
    user2_outfit_ids = [o["id"] for o in list_res.json()]
    assert outfit_id not in user2_outfit_ids
