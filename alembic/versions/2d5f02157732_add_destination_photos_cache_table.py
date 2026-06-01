"""add destination_photos cache table

Revision ID: 2d5f02157732
Revises: 2d9d0c3b1a5f
Create Date: 2026-06-01 14:58:23.627571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d5f02157732'
down_revision: Union[str, None] = '2d9d0c3b1a5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'destination_photos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cache_key', sa.String(length=220), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=120), nullable=True),
        sa.Column('photo_url', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('external_id', sa.String(length=120), nullable=True),
        sa.Column('photographer_name', sa.String(length=200), nullable=True),
        sa.Column('photographer_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key', 'external_id', name='uq_destination_photo_key_external'),
    )
    op.create_index(op.f('ix_destination_photos_cache_key'), 'destination_photos', ['cache_key'], unique=False)
    op.create_index(op.f('ix_destination_photos_city'), 'destination_photos', ['city'], unique=False)
    op.create_index(op.f('ix_destination_photos_country'), 'destination_photos', ['country'], unique=False)
    op.create_index(op.f('ix_destination_photos_id'), 'destination_photos', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_destination_photos_id'), table_name='destination_photos')
    op.drop_index(op.f('ix_destination_photos_country'), table_name='destination_photos')
    op.drop_index(op.f('ix_destination_photos_city'), table_name='destination_photos')
    op.drop_index(op.f('ix_destination_photos_cache_key'), table_name='destination_photos')
    op.drop_table('destination_photos')
