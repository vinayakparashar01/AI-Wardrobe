"""Tests for clothing items CRUD, authorization, validation, and image upload."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# 1. Authorization & Unauthenticated Access
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_clothing_endpoints(async_client: AsyncClient):
    """Unauthenticated requests to protected clothing endpoints must return 401."""
    random_id = str(uuid4())

    # GET list
    res_list = await async_client.get("/clothing-items/")
    assert res_list.status_code == 401

    # POST create
    res_create = await async_client.post(
        "/clothing-items/",
        data={"name": "Shirt", "category": "Upper", "color": "White"},
    )
    assert res_create.status_code == 401

    # GET single
    res_get = await async_client.get(f"/clothing-items/{random_id}")
    assert res_get.status_code == 401

    # PUT update
    res_update = await async_client.put(
        f"/clothing-items/{random_id}",
        data={"name": "Updated Shirt", "category": "Upper", "color": "Blue"},
    )
    assert res_update.status_code == 401

    # DELETE delete
    res_delete = await async_client.delete(f"/clothing-items/{random_id}")
    assert res_delete.status_code == 401


# ---------------------------------------------------------------------------
# 2. Clothing Items CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_clothing_item_success(async_client: AsyncClient, test_user: dict):
    """Authenticated user can create a clothing item without an image."""
    response = await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={
            "name": "Classic Denim Jacket",
            "category": "Upper",
            "color": "Blue",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Classic Denim Jacket"
    assert data["category"] == "Upper"
    assert data["color"] == "Blue"
    assert data["user_id"] == str(test_user["user"].id)
    assert data["image_url"] is None


@pytest.mark.asyncio
async def test_list_clothing_items(async_client: AsyncClient, test_user: dict):
    """Listing clothing items returns only items belonging to the current user."""
    # Initially empty
    res_empty = await async_client.get("/clothing-items/", headers=test_user["headers"])
    assert res_empty.status_code == 200
    assert res_empty.json() == []

    # Create two items
    await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"name": "Black T-Shirt", "category": "Upper", "color": "Black"},
    )
    await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"name": "Chino Trousers", "category": "Lower", "color": "Khaki"},
    )

    res_list = await async_client.get("/clothing-items/", headers=test_user["headers"])
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) == 2
    item_names = {i["name"] for i in items}
    assert item_names == {"Black T-Shirt", "Chino Trousers"}


@pytest.mark.asyncio
async def test_get_clothing_item_by_id(async_client: AsyncClient, test_user: dict):
    """Retrieve a single clothing item by its UUID."""
    create_res = await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"name": "Wool Sweater", "category": "Upper", "color": "Grey"},
    )
    item_id = create_res.json()["id"]

    get_res = await async_client.get(
        f"/clothing-items/{item_id}",
        headers=test_user["headers"],
    )
    assert get_res.status_code == 200
    item = get_res.json()
    assert item["id"] == item_id
    assert item["name"] == "Wool Sweater"
    assert item["category"] == "Upper"
    assert item["color"] == "Grey"


@pytest.mark.asyncio
async def test_get_clothing_item_not_found(async_client: AsyncClient, test_user: dict):
    """Retrieving a non-existent item UUID returns 404."""
    random_id = str(uuid4())
    response = await async_client.get(
        f"/clothing-items/{random_id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Clothing item not found"


@pytest.mark.asyncio
async def test_get_clothing_item_invalid_uuid(async_client: AsyncClient, test_user: dict):
    """Invalid UUID format in URL parameter returns 422 Unprocessable Entity."""
    response = await async_client.get(
        "/clothing-items/not-a-valid-uuid",
        headers=test_user["headers"],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_clothing_item(async_client: AsyncClient, test_user: dict):
    """Update an existing clothing item's details."""
    create_res = await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"name": "Old Name", "category": "Upper", "color": "Red"},
    )
    item_id = create_res.json()["id"]

    update_res = await async_client.put(
        f"/clothing-items/{item_id}",
        headers=test_user["headers"],
        data={"name": "New Name", "category": "Upper", "color": "Burgundy"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["name"] == "New Name"
    assert updated_data["color"] == "Burgundy"

    # Verify persistence by fetching again
    fetch_res = await async_client.get(
        f"/clothing-items/{item_id}",
        headers=test_user["headers"],
    )
    assert fetch_res.status_code == 200
    assert fetch_res.json()["name"] == "New Name"
    assert fetch_res.json()["color"] == "Burgundy"


@pytest.mark.asyncio
async def test_delete_clothing_item(async_client: AsyncClient, test_user: dict):
    """Delete an item returns 204 and item is no longer retrievable."""
    create_res = await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"name": "Temporary Boots", "category": "Shoes", "color": "Brown"},
    )
    item_id = create_res.json()["id"]

    delete_res = await async_client.delete(
        f"/clothing-items/{item_id}",
        headers=test_user["headers"],
    )
    assert delete_res.status_code == 204

    # Subsequent GET returns 404
    fetch_res = await async_client.get(
        f"/clothing-items/{item_id}",
        headers=test_user["headers"],
    )
    assert fetch_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_clothing_item(async_client: AsyncClient, test_user: dict):
    """Attempting to delete a non-existent item returns 404."""
    random_id = str(uuid4())
    delete_res = await async_client.delete(
        f"/clothing-items/{random_id}",
        headers=test_user["headers"],
    )
    assert delete_res.status_code == 404


# ---------------------------------------------------------------------------
# 3. Cross-User Isolation (Authorization Protection)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cross_user_isolation(
    async_client: AsyncClient,
    test_user: dict,
    second_user: dict,
):
    """One user must not be able to view, list, update, or delete another user's clothing items."""
    # User 1 creates an item
    create_res = await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"name": "User 1 Exclusive Jacket", "category": "Upper", "color": "Navy"},
    )
    user1_item_id = create_res.json()["id"]

    # User 2 lists items -> User 1's item must NOT appear
    user2_list = await async_client.get(
        "/clothing-items/",
        headers=second_user["headers"],
    )
    assert user2_list.status_code == 200
    assert not any(i["id"] == user1_item_id for i in user2_list.json())

    # User 2 tries to GET User 1's item -> 404
    user2_get = await async_client.get(
        f"/clothing-items/{user1_item_id}",
        headers=second_user["headers"],
    )
    assert user2_get.status_code == 404

    # User 2 tries to UPDATE User 1's item -> 404
    user2_update = await async_client.put(
        f"/clothing-items/{user1_item_id}",
        headers=second_user["headers"],
        data={"name": "Hijacked Jacket", "category": "Upper", "color": "Black"},
    )
    assert user2_update.status_code == 404

    # User 2 tries to DELETE User 1's item -> 404
    user2_delete = await async_client.delete(
        f"/clothing-items/{user1_item_id}",
        headers=second_user["headers"],
    )
    assert user2_delete.status_code == 404

    # User 1 verifies their item was NOT modified or deleted
    user1_verify = await async_client.get(
        f"/clothing-items/{user1_item_id}",
        headers=test_user["headers"],
    )
    assert user1_verify.status_code == 200
    assert user1_verify.json()["name"] == "User 1 Exclusive Jacket"


# ---------------------------------------------------------------------------
# 4. Input Validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_clothing_item_missing_required_fields(
    async_client: AsyncClient,
    test_user: dict,
):
    """Missing required form fields (name, category, color) returns 422."""
    # Missing name
    res1 = await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"category": "Upper", "color": "Red"},
    )
    assert res1.status_code == 422

    # Missing category
    res2 = await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"name": "Shirt", "color": "Red"},
    )
    assert res2.status_code == 422

    # Missing color
    res3 = await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"name": "Shirt", "category": "Upper"},
    )
    assert res3.status_code == 422


# ---------------------------------------------------------------------------
# 5. Image Upload Behavior
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clothing_item_with_valid_image_upload(
    async_client: AsyncClient,
    test_user: dict,
):
    """Creating a clothing item with a valid image file succeeds and returns image_url."""
    # 1x1 transparent PNG byte signature
    fake_png_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    response = await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"name": "Graphic Tee", "category": "Upper", "color": "Black"},
        files={"image": ("test_tee.png", fake_png_data, "image/png")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["image_url"] is not None
    assert data["image_url"].startswith("/media/")
    assert data["image_url"].endswith(".png")


@pytest.mark.asyncio
async def test_clothing_item_rejects_non_image_file(
    async_client: AsyncClient,
    test_user: dict,
):
    """Uploading a non-image file (e.g. text/plain) must be rejected with 400 Bad Request."""
    text_data = b"This is plain text, not a clothing photo."

    response = await async_client.post(
        "/clothing-items/",
        headers=test_user["headers"],
        data={"name": "Bad File Item", "category": "Upper", "color": "White"},
        files={"image": ("script.txt", text_data, "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only image files are allowed"
