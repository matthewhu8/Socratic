"""TASA knowledge model: question_kc, kc_mastery, student_personas, student_memory_events

Also merges the two open heads (a1b2c3d4e5f6 IB-KC tables, b8d2e87351dc) into one.

Revision ID: f1a2b3c4d5e6
Revises: a1b2c3d4e5f6, b8d2e87351dc
Create Date: 2026-07-04 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = ("a1b2c3d4e5f6", "b8d2e87351dc")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "question_kc",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("practice_mode", sa.String(), nullable=False),
        sa.Column("kc_id", sa.Integer(), sa.ForeignKey("knowledge_components.id"), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "practice_mode", "kc_id", name="uq_question_kc"),
    )
    op.create_index("ix_question_kc_id", "question_kc", ["id"])
    op.create_index("ix_question_kc_question_id", "question_kc", ["question_id"])

    op.create_table(
        "kc_mastery",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("student_users.id"), nullable=False),
        sa.Column("kc_id", sa.Integer(), sa.ForeignKey("knowledge_components.id"), nullable=False),
        sa.Column("p_mastery", sa.Float(), nullable=False),
        sa.Column("n_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("n_correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_practiced_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "kc_id", name="uq_kc_mastery_user_kc"),
    )
    op.create_index("ix_kc_mastery_id", "kc_mastery", ["id"])
    op.create_index("ix_kc_mastery_user_id", "kc_mastery", ["user_id"])
    op.create_index("ix_kc_mastery_kc_id", "kc_mastery", ["kc_id"])

    op.create_table(
        "student_personas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("student_users.id"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("concept_keywords", sa.JSON(), nullable=True),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_personas_id", "student_personas", ["id"])
    op.create_index("ix_student_personas_user_id", "student_personas", ["user_id"])

    op.create_table(
        "student_memory_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("student_users.id"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("concept_keywords", sa.JSON(), nullable=True),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("event_at", sa.DateTime(), nullable=True),
        sa.Column("source_grading_id", sa.Integer(), sa.ForeignKey("grading_sessions.id"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_memory_events_id", "student_memory_events", ["id"])
    op.create_index("ix_student_memory_events_user_id", "student_memory_events", ["user_id"])


def downgrade() -> None:
    op.drop_table("student_memory_events")
    op.drop_table("student_personas")
    op.drop_table("kc_mastery")
    op.drop_table("question_kc")
