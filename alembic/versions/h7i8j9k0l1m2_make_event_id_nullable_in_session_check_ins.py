"""make_event_id_nullable_in_session_check_ins

Revision ID: h7i8j9k0l1m2
Revises: g6h7i8j9k0l1
Create Date: 2025-11-30 09:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'h7i8j9k0l1m2'
down_revision = 'g6h7i8j9k0l1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make event_id nullable in session_check_ins
    # This allows TIME_BASED subscriptions to create check-in records without an event
    op.alter_column('session_check_ins', 'event_id',
                   existing_type=sa.String(36),
                   nullable=True)


def downgrade() -> None:
    # Revert event_id to non-nullable
    op.alter_column('session_check_ins', 'event_id',
                   existing_type=sa.String(36),
                   nullable=False)
