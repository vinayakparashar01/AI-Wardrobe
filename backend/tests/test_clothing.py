"""Tests for clothing items CRUD, authorization, validation, and image upload."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.utils.files import CloudinaryUploadResult


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

    mock_secure_url = (
        "https://res.cloudinary.com/demo/image/upload/v1234567890/clothing/test_tee.png"
    )
    mock_public_id = "clothing/test_tee"
    mock_result = CloudinaryUploadResult(
        secure_url=mock_secure_url,
        public_id=mock_public_id,
    )

    with patch(
        "app.services.clothing_service.upload_image_to_cloudinary",
        return_value=mock_result,
    ) as mock_upload:
        response = await async_client.post(
            "/clothing-items/",
            headers=test_user["headers"],
            data={"name": "Graphic Tee", "category": "Upper", "color": "Black"},
            files={"image": ("test_tee.png", fake_png_data, "image/png")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["name"] == "Graphic Tee"
        assert data["category"] == "Upper"
        assert data["color"] == "Black"
        assert data["image_url"] == mock_secure_url
        assert mock_upload.called

    # Ensure the uploaded image URL is saved to the clothing item in the database
    fetch_res = await async_client.get(
        f"/clothing-items/{data['id']}",
        headers=test_user["headers"],
    )
    assert fetch_res.status_code == 200
    assert fetch_res.json()["image_url"] == mock_secure_url


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


# ---------------------------------------------------------------------------
# 6. Image Removal, Replacement & Persistence on Update
# ---------------------------------------------------------------------------

FAKE_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.mark.asyncio
async def test_update_clothing_keep_existing_image(
    async_client: AsyncClient,
    test_user: dict,
):
    """Case A: Updating clothing details without image and remove_image=False preserves existing image."""
    mock_url = "https://res.cloudinary.com/demo/image/upload/v1/clothing/original.png"
    mock_result = CloudinaryUploadResult(secure_url=mock_url, public_id="clothing/original")

    with patch("app.services.clothing_service.upload_image_to_cloudinary", return_value=mock_result):
        create_res = await async_client.post(
            "/clothing-items/",
            headers=test_user["headers"],
            data={"name": "Original Tee", "category": "Upper", "color": "White"},
            files={"image": ("original.png", FAKE_PNG_BYTES, "image/png")},
        )
    assert create_res.status_code == 201
    item_id = create_res.json()["id"]
    assert create_res.json()["image_url"] == mock_url

    with patch("app.services.clothing_service.delete_image_file") as mock_delete:
        update_res = await async_client.put(
            f"/clothing-items/{item_id}",
            headers=test_user["headers"],
            data={
                "name": "Updated Tee",
                "category": "Upper",
                "color": "Off-White",
                "remove_image": "false",
            },
        )
        assert update_res.status_code == 200
        updated_data = update_res.json()
        assert updated_data["name"] == "Updated Tee"
        assert updated_data["image_url"] == mock_url
        assert not mock_delete.called

    # Verify DB persistence
    fetch_res = await async_client.get(f"/clothing-items/{item_id}", headers=test_user["headers"])
    assert fetch_res.status_code == 200
    assert fetch_res.json()["image_url"] == mock_url


@pytest.mark.asyncio
async def test_update_clothing_remove_image_success(
    async_client: AsyncClient,
    test_user: dict,
):
    """Case B: Updating clothing with remove_image=True sets image_url to None and deletes storage file."""
    mock_url = "https://res.cloudinary.com/demo/image/upload/v1/clothing/to_remove.png"
    mock_result = CloudinaryUploadResult(secure_url=mock_url, public_id="clothing/to_remove")

    with patch("app.services.clothing_service.upload_image_to_cloudinary", return_value=mock_result):
        create_res = await async_client.post(
            "/clothing-items/",
            headers=test_user["headers"],
            data={"name": "Shirt To Clear", "category": "Upper", "color": "Blue"},
            files={"image": ("to_remove.png", FAKE_PNG_BYTES, "image/png")},
        )
    item_id = create_res.json()["id"]
    assert create_res.json()["image_url"] == mock_url

    with patch("app.services.clothing_service.delete_image_file") as mock_delete:
        update_res = await async_client.put(
            f"/clothing-items/{item_id}",
            headers=test_user["headers"],
            data={
                "name": "Shirt Without Photo",
                "category": "Upper",
                "color": "Blue",
                "remove_image": "true",
            },
        )
        assert update_res.status_code == 200
        updated_data = update_res.json()
        assert updated_data["image_url"] is None
        mock_delete.assert_called_once_with(mock_url)

    # Verify DB persistence: image_url is null
    fetch_res = await async_client.get(f"/clothing-items/{item_id}", headers=test_user["headers"])
    assert fetch_res.status_code == 200
    assert fetch_res.json()["image_url"] is None


@pytest.mark.asyncio
async def test_update_clothing_replace_image_success(
    async_client: AsyncClient,
    test_user: dict,
):
    """Case C: Uploading a new image updates image_url and deletes the old image."""
    old_url = "https://res.cloudinary.com/demo/image/upload/v1/clothing/old_look.png"
    new_url = "https://res.cloudinary.com/demo/image/upload/v2/clothing/new_look.png"

    res_old = CloudinaryUploadResult(secure_url=old_url, public_id="clothing/old_look")
    res_new = CloudinaryUploadResult(secure_url=new_url, public_id="clothing/new_look")

    with patch("app.services.clothing_service.upload_image_to_cloudinary", return_value=res_old):
        create_res = await async_client.post(
            "/clothing-items/",
            headers=test_user["headers"],
            data={"name": "Pants", "category": "Lower", "color": "Grey"},
            files={"image": ("old.png", FAKE_PNG_BYTES, "image/png")},
        )
    item_id = create_res.json()["id"]

    with patch(
        "app.services.clothing_service.upload_image_to_cloudinary", return_value=res_new
    ), patch("app.services.clothing_service.delete_image_file") as mock_delete:
        update_res = await async_client.put(
            f"/clothing-items/{item_id}",
            headers=test_user["headers"],
            data={"name": "Upgraded Pants", "category": "Lower", "color": "Charcoal"},
            files={"image": ("new.png", FAKE_PNG_BYTES, "image/png")},
        )
        assert update_res.status_code == 200
        assert update_res.json()["image_url"] == new_url
        # Old image must be deleted
        mock_delete.assert_called_once_with(old_url)

    # Verify DB persistence
    fetch_res = await async_client.get(f"/clothing-items/{item_id}", headers=test_user["headers"])
    assert fetch_res.status_code == 200
    assert fetch_res.json()["image_url"] == new_url


@pytest.mark.asyncio
async def test_update_clothing_prioritize_new_image_over_remove_flag(
    async_client: AsyncClient,
    test_user: dict,
):
    """When both a new image and remove_image=true are sent, the new image must be prioritized."""
    old_url = "https://res.cloudinary.com/demo/image/upload/v1/clothing/first.png"
    replacement_url = "https://res.cloudinary.com/demo/image/upload/v2/clothing/second.png"

    res_first = CloudinaryUploadResult(secure_url=old_url, public_id="clothing/first")
    res_second = CloudinaryUploadResult(secure_url=replacement_url, public_id="clothing/second")

    with patch("app.services.clothing_service.upload_image_to_cloudinary", return_value=res_first):
        create_res = await async_client.post(
            "/clothing-items/",
            headers=test_user["headers"],
            data={"name": "Jacket", "category": "Upper", "color": "Black"},
            files={"image": ("first.png", FAKE_PNG_BYTES, "image/png")},
        )
    item_id = create_res.json()["id"]

    with patch(
        "app.services.clothing_service.upload_image_to_cloudinary", return_value=res_second
    ), patch("app.services.clothing_service.delete_image_file") as mock_delete:
        update_res = await async_client.put(
            f"/clothing-items/{item_id}",
            headers=test_user["headers"],
            data={
                "name": "Jacket",
                "category": "Upper",
                "color": "Black",
                "remove_image": "true",  # Conflicting flag
            },
            files={"image": ("second.png", FAKE_PNG_BYTES, "image/png")},
        )
        assert update_res.status_code == 200
        assert update_res.json()["image_url"] == replacement_url
        mock_delete.assert_called_once_with(old_url)


@pytest.mark.asyncio
async def test_remove_image_does_not_affect_other_items(
    async_client: AsyncClient,
    test_user: dict,
):
    """Removing one item's image never deletes or alters another clothing item's image."""
    url1 = "https://res.cloudinary.com/demo/image/upload/v1/clothing/item1.png"
    url2 = "https://res.cloudinary.com/demo/image/upload/v1/clothing/item2.png"

    with patch(
        "app.services.clothing_service.upload_image_to_cloudinary",
        return_value=CloudinaryUploadResult(secure_url=url1, public_id="clothing/item1"),
    ):
        res1 = await async_client.post(
            "/clothing-items/",
            headers=test_user["headers"],
            data={"name": "Item 1", "category": "Upper", "color": "Red"},
            files={"image": ("item1.png", FAKE_PNG_BYTES, "image/png")},
        )
    with patch(
        "app.services.clothing_service.upload_image_to_cloudinary",
        return_value=CloudinaryUploadResult(secure_url=url2, public_id="clothing/item2"),
    ):
        res2 = await async_client.post(
            "/clothing-items/",
            headers=test_user["headers"],
            data={"name": "Item 2", "category": "Lower", "color": "Blue"},
            files={"image": ("item2.png", FAKE_PNG_BYTES, "image/png")},
        )

    id1 = res1.json()["id"]
    id2 = res2.json()["id"]

    # Remove image from Item 1
    with patch("app.services.clothing_service.delete_image_file") as mock_delete:
        update_res = await async_client.put(
            f"/clothing-items/{id1}",
            headers=test_user["headers"],
            data={
                "name": "Item 1",
                "category": "Upper",
                "color": "Red",
                "remove_image": "true",
            },
        )
        assert update_res.status_code == 200
        assert update_res.json()["image_url"] is None
        mock_delete.assert_called_once_with(url1)

    # Item 2's image must be intact
    fetch2 = await async_client.get(f"/clothing-items/{id2}", headers=test_user["headers"])
    assert fetch2.status_code == 200
    assert fetch2.json()["image_url"] == url2


@pytest.mark.asyncio
async def test_database_failure_does_not_delete_old_image(
    async_client: AsyncClient,
    test_user: dict,
):
    """If database update fails during image removal, the old image must NOT be deleted."""
    mock_url = "https://res.cloudinary.com/demo/image/upload/v1/clothing/preserve_on_err.png"
    mock_result = CloudinaryUploadResult(secure_url=mock_url, public_id="clothing/preserve_on_err")

    with patch("app.services.clothing_service.upload_image_to_cloudinary", return_value=mock_result):
        create_res = await async_client.post(
            "/clothing-items/",
            headers=test_user["headers"],
            data={"name": "Safe Item", "category": "Upper", "color": "Green"},
            files={"image": ("safe.png", FAKE_PNG_BYTES, "image/png")},
        )
    item_id = create_res.json()["id"]

    # Simulate database commit error
    with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=RuntimeError("DB Commit Failed")), \
         patch("app.services.clothing_service.delete_image_file") as mock_delete:
        with pytest.raises(RuntimeError, match="DB Commit Failed"):
            await async_client.put(
                f"/clothing-items/{item_id}",
                headers=test_user["headers"],
                data={
                    "name": "Safe Item",
                    "category": "Upper",
                    "color": "Green",
                    "remove_image": "true",
                },
            )
        # Old image was NOT deleted because transaction failed
        assert not mock_delete.called

    # Item in DB still has its old image
    fetch_res = await async_client.get(f"/clothing-items/{item_id}", headers=test_user["headers"])
    assert fetch_res.status_code == 200
    assert fetch_res.json()["image_url"] == mock_url


@pytest.mark.asyncio
async def test_database_failure_cleans_up_new_image_and_preserves_old(
    async_client: AsyncClient,
    test_user: dict,
):
    """If database update fails during image replacement, clean up the newly uploaded image and do not delete the old image."""
    old_url = "https://res.cloudinary.com/demo/image/upload/v1/clothing/original_kept.png"
    new_url = "https://res.cloudinary.com/demo/image/upload/v2/clothing/failed_new.png"

    res_old = CloudinaryUploadResult(secure_url=old_url, public_id="clothing/original_kept")
    res_new = CloudinaryUploadResult(secure_url=new_url, public_id="clothing/failed_new")

    with patch("app.services.clothing_service.upload_image_to_cloudinary", return_value=res_old):
        create_res = await async_client.post(
            "/clothing-items/",
            headers=test_user["headers"],
            data={"name": "Initial Shirt", "category": "Upper", "color": "White"},
            files={"image": ("old.png", FAKE_PNG_BYTES, "image/png")},
        )
    item_id = create_res.json()["id"]

    # Simulate database commit error
    with patch("app.services.clothing_service.upload_image_to_cloudinary", return_value=res_new), \
         patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=RuntimeError("DB Commit Failed")), \
         patch("app.services.clothing_service.delete_image_file") as mock_delete:
        with pytest.raises(RuntimeError, match="DB Commit Failed"):
            await async_client.put(
                f"/clothing-items/{item_id}",
                headers=test_user["headers"],
                data={
                    "name": "New Shirt",
                    "category": "Upper",
                    "color": "White",
                },
                files={"image": ("new.png", FAKE_PNG_BYTES, "image/png")},
            )
        # Newly uploaded image was cleaned up, old image was NOT deleted
        mock_delete.assert_called_once_with(new_url)

    # Item in DB still retains the original image
    fetch_res = await async_client.get(f"/clothing-items/{item_id}", headers=test_user["headers"])
    assert fetch_res.status_code == 200
    assert fetch_res.json()["image_url"] == old_url
