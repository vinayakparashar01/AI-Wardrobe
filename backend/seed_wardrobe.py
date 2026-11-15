import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import UUID

from app.db.database import engine
from app.models.clothing_item import ClothingItem
from sqlalchemy.ext.asyncio import AsyncSession

USER_ID = UUID("540d05b0-671e-4ea6-a42b-a2ee9f33febc")


async def seed_wardrobe():
    env = os.environ.get("ENVIRONMENT", "development").strip().lower()
    if env in ("production", "prod"):
        print(
            "Error: Seeding is blocked in production environment (ENVIRONMENT=production).",
            file=sys.stderr,
        )
        raise RuntimeError("Seeding is blocked in production environment.")

    repo_root = Path(__file__).resolve().parent.parent
    json_path = repo_root / "sample_wardrobe.json"
    if not json_path.exists():
        json_path = Path(__file__).resolve().parent / "sample_wardrobe.json"

    data = json.loads(json_path.read_text(encoding="utf-8"))

    async with AsyncSession(engine) as db:
        items = [
            ClothingItem(
                user_id=USER_ID,
                name=item["name"],
                category=item["category"],
                color=item["color"],
                image_url=None,
            )
            for item in data
        ]

        db.add_all(items)

        await db.commit()

        print(f"Added {len(items)} clothing items.")


if __name__ == "__main__":
    try:
        asyncio.run(seed_wardrobe())
    except RuntimeError:
        sys.exit(1)
