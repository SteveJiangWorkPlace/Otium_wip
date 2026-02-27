"""Add background_tasks table for background worker

Revision ID: af7f0ba9b1a8
Revises: ecd2cc2e9e99
Create Date: 2026-02-27 19:50:00.000000

"""
from collections.abc import Sequence

import logging
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "af7f0ba9b1a8"
down_revision: str | Sequence[str] | None = "ecd2cc2e9e99"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create background_tasks table
    op.create_table(
        "background_tasks",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), default="pending", nullable=False),
        sa.Column("request_data", sa.Text, nullable=True),
        sa.Column("result_data", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("attempts", sa.Integer, default=0),
        sa.Column("max_attempts", sa.Integer, default=3),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        # 进度跟踪字段
        sa.Column("progress_percentage", sa.Integer, default=0),  # 进度百分比（0-100）
        sa.Column("current_step", sa.Integer, default=0),  # 当前步骤索引（从0开始）
        sa.Column("total_steps", sa.Integer, default=1),  # 总步骤数
        sa.Column("step_description", sa.String(500), nullable=True),  # 当前步骤描述
        sa.Column("step_details", sa.Text, nullable=True),  # 详细进度信息（JSON字符串）
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes
    op.create_index(op.f("ix_background_tasks_user_id"), "background_tasks", ["user_id"])
    op.create_index(op.f("ix_background_tasks_status"), "background_tasks", ["status"])
    op.create_index(op.f("ix_background_tasks_created_at"), "background_tasks", ["created_at"])

    logging.info("Created background_tasks table for background worker")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f("ix_background_tasks_created_at"), table_name="background_tasks")
    op.drop_index(op.f("ix_background_tasks_status"), table_name="background_tasks")
    op.drop_index(op.f("ix_background_tasks_user_id"), table_name="background_tasks")

    # Drop table
    op.drop_table("background_tasks")

    logging.info("Dropped background_tasks table")