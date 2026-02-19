"""add banner_photo_url to trips

Revision ID: 2d9d0c3b1a5f
Revises: 6b9e8b3a2f1a
Create Date: 2026-02-19 07:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2d9d0c3b1a5f'
down_revision: Union[str, None] = '6b9e8b3a2f1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('trips', sa.Column('banner_photo_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('trips', 'banner_photo_url')
