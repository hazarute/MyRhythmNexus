"""add_subscription_id_to_class_events

Revision ID: d1e2f3g4h5i6
Revises: b33fd22c4fa0
Create Date: 2025-11-29 21:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd1e2f3g4h5i6'
down_revision = 'b33fd22c4fa0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add subscription_id column to class_events with CASCADE delete foreign key
    op.add_column('class_events', sa.Column('subscription_id', sa.String(36), nullable=True))
    op.create_foreign_key(
        'fk_class_events_subscription_id',
        'class_events',
        'subscriptions',
        ['subscription_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop foreign key and column
    op.drop_constraint('fk_class_events_subscription_id', 'class_events', type_='foreignkey')
    op.drop_column('class_events', 'subscription_id')
