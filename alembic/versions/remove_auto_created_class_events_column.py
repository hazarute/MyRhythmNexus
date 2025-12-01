"""remove_auto_created_class_events_column

Revision ID: e4f5g6h7i8j9
Revises: d1e2f3g4h5i6
Create Date: 2025-11-29 21:45:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e4f5g6h7i8j9'
down_revision = 'd1e2f3g4h5i6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop auto_created_class_events column - it's now a relationship only
    op.drop_column('subscriptions', 'auto_created_class_events')


def downgrade() -> None:
    # Add back the column if needed
    op.add_column('subscriptions', sa.Column('auto_created_class_events', sa.Boolean(), nullable=False, server_default=sa.false()))
