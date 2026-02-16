"""remove activity photo_url

Revision ID: 7dc7b8dd3542
Revises: 6486e116ae51
Create Date: 2026-02-16 10:59:15.400571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7dc7b8dd3542'
down_revision: Union[str, None] = '6486e116ae51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('activities', 'photo_url')


def downgrade() -> None:
    op.add_column('activities', sa.Column('photo_url', sa.Text(), nullable=True))
