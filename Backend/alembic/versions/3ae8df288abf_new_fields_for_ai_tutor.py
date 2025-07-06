"""new_fields_for_ai_tutor

Revision ID: 3ae8df288abf
Revises: 0cddcb5df654
Create Date: 2025-07-06 01:24:22.262204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ae8df288abf'
down_revision: Union[str, Sequence[str], None] = '0cddcb5df654'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
