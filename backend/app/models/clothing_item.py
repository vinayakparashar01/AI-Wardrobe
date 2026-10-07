from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.db.database import Base
from app.models.user import User
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.outfit_item import OutfitItem


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(100))

    category: Mapped[str] = mapped_column(String(50))

    color: Mapped[str] = mapped_column(String(50))

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    user: Mapped["User"] = relationship(back_populates="clothing_items")

    outfit_items: Mapped[list["OutfitItem"]] = relationship(
        back_populates="clothing_item",
    )
