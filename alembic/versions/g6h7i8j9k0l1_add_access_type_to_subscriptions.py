"""add_access_type_to_subscriptions

Revision ID: g6h7i8j9k0l1
Revises: f5g6h7i8j9k0
Create Date: 2025-11-30 09:20:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'g6h7i8j9k0l1'
down_revision = 'f5g6h7i8j9k0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add access_type column to subscriptions table
    # Default value: 'SESSION_BASED' (infer from package's plan_definition)
    op.add_column('subscriptions',
        sa.Column('access_type', sa.String(20), nullable=False, server_default='SESSION_BASED')
    )
    
    # Update existing subscriptions based on package's plan_definition access_type
    op.execute("""
        UPDATE subscriptions s
        SET access_type = COALESCE(pd.access_type, 'SESSION_BASED')
        FROM service_packages sp
        JOIN plan_definitions pd ON sp.plan_id = pd.id
        WHERE s.package_id = sp.id
    """)


def downgrade() -> None:
    # Drop access_type column
    op.drop_column('subscriptions', 'access_type')
