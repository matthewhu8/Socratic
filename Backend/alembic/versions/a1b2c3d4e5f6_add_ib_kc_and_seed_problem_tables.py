"""add IB KC and seed problem tables

Revision ID: a1b2c3d4e5f6
Revises: dad5d9f1dc17
Create Date: 2026-06-28 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "dad5d9f1dc17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_components",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("ib_topic_ref", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty_tier", sa.String(), nullable=False),
        sa.Column("curriculum", sa.String(), nullable=False, server_default="IB_Math_AA_SL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_components_id", "knowledge_components", ["id"])
    op.create_index("ix_knowledge_components_slug", "knowledge_components", ["slug"], unique=True)

    op.create_table(
        "kc_prerequisite",
        sa.Column("kc_id", sa.Integer(), sa.ForeignKey("knowledge_components.id"), primary_key=True),
        sa.Column("prereq_id", sa.Integer(), sa.ForeignKey("knowledge_components.id"), primary_key=True),
    )

    op.create_table(
        "seed_problems",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("command_term", sa.String(), nullable=False),
        sa.Column("ib_topic_ref", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("difficulty_tier", sa.String(), nullable=False),
        sa.Column("difficulty_estimate", sa.Float(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("worked_solution", sa.Text(), nullable=False),
        sa.Column("distractors", sa.JSON(), nullable=True),
        sa.Column("hint_l1", sa.Text(), nullable=False),
        sa.Column("hint_l2", sa.Text(), nullable=False),
        sa.Column("hint_l3", sa.Text(), nullable=False),
        sa.Column("re_solve_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("curriculum", sa.String(), nullable=False, server_default="IB_Math_AA_SL"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seed_problems_id", "seed_problems", ["id"])
    op.create_index("ix_seed_problems_slug", "seed_problems", ["slug"], unique=True)

    op.create_table(
        "seed_problem_kc",
        sa.Column("seed_problem_id", sa.Integer(), sa.ForeignKey("seed_problems.id"), primary_key=True),
        sa.Column("knowledge_component_id", sa.Integer(), sa.ForeignKey("knowledge_components.id"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("seed_problem_kc")
    op.drop_table("seed_problems")
    op.drop_table("kc_prerequisite")
    op.drop_index("ix_knowledge_components_slug", table_name="knowledge_components")
    op.drop_index("ix_knowledge_components_id", table_name="knowledge_components")
    op.drop_table("knowledge_components")
