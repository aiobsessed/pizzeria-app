"""add canceled to orderstatus enum

Revision ID: a47f64773f13
Revises: 67c1155ef836
Create Date: 2026-05-04 11:17:44.448503

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a47f64773f13"
down_revision: Union[str, Sequence[str], None] = "67c1155ef836"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE orderstatus ADD VALUE 'canceled'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
