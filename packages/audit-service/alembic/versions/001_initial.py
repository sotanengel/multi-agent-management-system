"""initial migration

Revision ID: 001_initial
Revises:
Create Date: 2026-05-23 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_entries",
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_num", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("prev_hash", sa.Text(), nullable=False),
        sa.Column("entry_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("entry_id"),
    )
    op.create_index(
        "ix_audit_entries_agent_id",
        "audit_entries",
        ["agent_id"],
    )
    op.create_index(
        "ix_audit_entries_agent_id_seq",
        "audit_entries",
        ["agent_id", "sequence_num"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_entries_agent_id_seq", table_name="audit_entries")
    op.drop_index("ix_audit_entries_agent_id", table_name="audit_entries")
    op.drop_table("audit_entries")
