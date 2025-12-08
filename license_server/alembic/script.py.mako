"""Auto-generated Alembic script template.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '${up_revision}'
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

def upgrade() -> None:
    """Upgrade migrations."""
    ${upgrades if upgrades else 'pass'}


def downgrade() -> None:
    """Downgrade migrations."""
    ${downgrades if downgrades else 'pass'}
