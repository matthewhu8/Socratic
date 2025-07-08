"""new_fields_for_ai_tutor

Revision ID: dad5d9f1dc17
Revises: 3ae8df288abf
Create Date: 2025-07-06 17:49:35.764220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dad5d9f1dc17'
down_revision: Union[str, Sequence[str], None] = '3ae8df288abf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
