"""new_fields

Revision ID: 3fa25416e3a8
Revises: dad5d9f1dc17
Create Date: 2025-07-08 23:41:30.784617

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fa25416e3a8'
down_revision: Union[str, Sequence[str], None] = 'dad5d9f1dc17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
