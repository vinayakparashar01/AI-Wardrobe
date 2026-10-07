import asyncio
import json
from pathlib import Path
from uuid import UUID

from app.db.database import engine
from app.models.clothing_item import ClothingItem
from sqlalchemy.ext.asyncio import AsyncSession

USER_ID = UUID("540d05b0-671e-4ea6-a42b-a2ee9f33febc")


async def seed_wardrobe():
    data = json.loads(
        (Path(__file__).parent / "sample_wardrobe.json").read_text(
            encoding="utf-8"
        )
    )

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
    asyncio.run(seed_wardrobe())
