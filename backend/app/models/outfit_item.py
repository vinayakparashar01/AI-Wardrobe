from datetime import datetime
from uuid import UUID, uuid4

from app.db.database import Base
from app.models.clothing_item import ClothingItem
from app.models.outfit import Outfit
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class OutfitItem(Base):
    __tablename__ = "outfit_items"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    outfit_id: Mapped[UUID] = mapped_column(
        ForeignKey("outfits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    clothing_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("clothing_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    outfit: Mapped["Outfit"] = relationship(
        back_populates="outfit_items"
    )

    clothing_item: Mapped["ClothingItem"] = relationship(
        back_populates="outfit_items"
    )
