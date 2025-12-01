"""add_repeat_weeks_to_plan_definition

Revision ID: c2a9e8b4f1d3
Revises: aef2d31489f2
Create Date: 2025-11-29 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c2a9e8b4f1d3'
down_revision = 'aef2d31489f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'plan_definitions',
        sa.Column('repeat_weeks', sa.Integer(), nullable=False, server_default='1')
    )
    op.alter_column(
        'plan_definitions',
        'repeat_weeks',
        server_default=None
    )


def downgrade() -> None:
    op.drop_column('plan_definitions', 'repeat_weeks')
