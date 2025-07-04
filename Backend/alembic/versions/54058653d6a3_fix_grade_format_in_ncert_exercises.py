"""fix_grade_format_in_ncert_exercises

Revision ID: 54058653d6a3
Revises: 40a0392caa0a
Create Date: 2025-07-04 01:44:12.839708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54058653d6a3'
down_revision: Union[str, Sequence[str], None] = '40a0392caa0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Update grade values from 'grade-10' format to just '10'
    op.execute("""
        UPDATE ncert_exercises 
        SET grade = REPLACE(grade, 'grade-', '') 
        WHERE grade LIKE 'grade-%'
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert grade values back to 'grade-10' format
    op.execute("""
        UPDATE ncert_exercises 
        SET grade = CONCAT('grade-', grade) 
        WHERE grade ~ '^[0-9]+$'
    """)
