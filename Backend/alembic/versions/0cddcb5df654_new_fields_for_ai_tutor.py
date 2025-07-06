"""new_fields_for_ai_tutor

Revision ID: 0cddcb5df654
Revises: 54058653d6a3
Create Date: 2025-07-06 01:23:22.993522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cddcb5df654'
down_revision: Union[str, Sequence[str], None] = '54058653d6a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
