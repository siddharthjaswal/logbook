"""add activity end_time

Revision ID: 6b9e8b3a2f1a
Revises: b3f0d5b9b2d1
Create Date: 2026-02-17 08:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b9e8b3a2f1a'
down_revision: Union[str, None] = 'b3f0d5b9b2d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('end_time', sa.String(5), nullable=True))


def downgrade() -> None:
    op.drop_column('activities', 'end_time')
