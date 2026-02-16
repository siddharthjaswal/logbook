"""add activity photo_url

Revision ID: 6486e116ae51
Revises: 66d3b9e05e39
Create Date: 2026-02-16 09:14:18.454138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6486e116ae51'
down_revision: Union[str, None] = '66d3b9e05e39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('photo_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('activities', 'photo_url')
