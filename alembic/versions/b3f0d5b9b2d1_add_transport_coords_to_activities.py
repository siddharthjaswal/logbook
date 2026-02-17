"""add transport coords to activities

Revision ID: b3f0d5b9b2d1
Revises: 7dc7b8dd3542
Create Date: 2026-02-17 08:13:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f0d5b9b2d1'
down_revision: Union[str, None] = '7dc7b8dd3542'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('start_latitude', sa.DECIMAL(10, 8), nullable=True))
    op.add_column('activities', sa.Column('start_longitude', sa.DECIMAL(11, 8), nullable=True))
    op.add_column('activities', sa.Column('end_latitude', sa.DECIMAL(10, 8), nullable=True))
    op.add_column('activities', sa.Column('end_longitude', sa.DECIMAL(11, 8), nullable=True))


def downgrade() -> None:
    op.drop_column('activities', 'end_longitude')
    op.drop_column('activities', 'end_latitude')
    op.drop_column('activities', 'start_longitude')
    op.drop_column('activities', 'start_latitude')
