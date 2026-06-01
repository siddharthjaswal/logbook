"""add unit_system to users

Revision ID: a1c3e5f7b9d2
Revises: 2d5f02157732
Create Date: 2026-06-01 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1c3e5f7b9d2'
down_revision: Union[str, None] = '2d5f02157732'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('unit_system', sa.String(length=10), nullable=False, server_default='metric'),
    )


def downgrade() -> None:
    op.drop_column('users', 'unit_system')
