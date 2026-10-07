"""rename favourite to favorite

Revision ID: 9485ff946b5f
Revises: bf47932780ff
Create Date: 2026-09-10 00:03:38.236987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9485ff946b5f'
down_revision: Union[str, Sequence[str], None] = 'bf47932780ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "outfits",
        "is_favourite",
        new_column_name="is_favorite",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "outfits",
        "is_favorite",
        new_column_name="is_favourite",
    )
