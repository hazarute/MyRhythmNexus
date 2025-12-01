"""add_access_type_to_plan_definition

Revision ID: aef2d31489f2
Revises: 1060e243cb3d
Create Date: 2025-11-29 00:40:13.977890
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'aef2d31489f2'
down_revision = '1060e243cb3d'
branch_labels = None
depends_on = None




def upgrade() -> None:
    # Add access_type column with default value 'SESSION_BASED'
    op.add_column('plan_definitions', 
        sa.Column('access_type', sa.String(20), nullable=False, server_default='SESSION_BASED')
    )
    
    # Update existing plans: If sessions_granted = 0, set to TIME_BASED
    op.execute("""
        UPDATE plan_definitions 
        SET access_type = 'TIME_BASED' 
        WHERE sessions_granted = 0
    """)
    
    # Make sessions_granted nullable for TIME_BASED plans
    op.alter_column('plan_definitions', 'sessions_granted',
                   existing_type=sa.Integer(),
                   nullable=True)


def downgrade() -> None:
    # Revert sessions_granted to non-nullable (set 0 for TIME_BASED plans)
    op.execute("""
        UPDATE plan_definitions 
        SET sessions_granted = 0 
        WHERE access_type = 'TIME_BASED'
    """)
    
    op.alter_column('plan_definitions', 'sessions_granted',
                   existing_type=sa.Integer(),
                   nullable=False)
    
    # Drop access_type column
    op.drop_column('plan_definitions', 'access_type')