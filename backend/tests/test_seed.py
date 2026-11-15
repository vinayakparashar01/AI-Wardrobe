"""Tests for seed script environment safety guards and execution."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from seed_wardrobe import seed_wardrobe


@pytest.mark.asyncio
async def test_seed_blocked_in_production(monkeypatch, capsys):
    """Running seed_wardrobe when ENVIRONMENT=production must raise RuntimeError and print to stderr."""
    monkeypatch.setenv("ENVIRONMENT", "production")

    with pytest.raises(RuntimeError, match="Seeding is blocked in production environment"):
        await seed_wardrobe()

    captured = capsys.readouterr()
    assert "Error: Seeding is blocked in production environment (ENVIRONMENT=production)." in captured.err


@pytest.mark.asyncio
async def test_seed_blocked_in_prod_shorthand(monkeypatch, capsys):
    """Running seed_wardrobe when ENVIRONMENT=prod must also be blocked."""
    monkeypatch.setenv("ENVIRONMENT", "prod")

    with pytest.raises(RuntimeError, match="Seeding is blocked in production environment"):
        await seed_wardrobe()

    captured = capsys.readouterr()
    assert "Error: Seeding is blocked in production environment" in captured.err


@pytest.mark.asyncio
async def test_seed_allowed_in_development(monkeypatch, capsys):
    """In development mode, seed_wardrobe parses the sample JSON and seeds the database."""
    monkeypatch.setenv("ENVIRONMENT", "development")

    mock_db = AsyncMock()
    mock_db.add_all = MagicMock()
    mock_db_cm = AsyncMock()
    mock_db_cm.__aenter__.return_value = mock_db
    mock_db_cm.__aexit__.return_value = None

    with patch("seed_wardrobe.AsyncSession", return_value=mock_db_cm):
        await seed_wardrobe()

    assert mock_db.add_all.called
    added_items = mock_db.add_all.call_args[0][0]
    assert len(added_items) == 17
    assert mock_db.commit.called

    captured = capsys.readouterr()
    assert "Added 17 clothing items." in captured.out
