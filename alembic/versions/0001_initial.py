"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-08 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column(
            "type",
            sa.Enum("PROCEDURE", "FAQ", "PROTOCOL", "GENERAL", name="document_type"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PROCESSING", "INDEXED", "ERROR", name="document_status"),
            nullable=False,
        ),
        sa.Column("chunks_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash"),
    )

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("whatsapp_number_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "CLOSED", "ESCALATED", name="conversation_status"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_message_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolved_without_human", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_whatsapp_number_hash", "conversations", ["whatsapp_number_hash"])

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(dim=1536), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_ivfflat "
        "ON document_chunks USING ivfflat (embedding vector_cosine_ops);"
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Enum("USER", "ASSISTANT", "SYSTEM", name="message_role"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources_used", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_ivfflat;")
    op.drop_table("document_chunks")
    op.drop_table("settings")
    op.drop_index("ix_conversations_whatsapp_number_hash", table_name="conversations")
    op.drop_table("conversations")
    op.drop_table("documents")

    op.execute("DROP TYPE IF EXISTS message_role;")
    op.execute("DROP TYPE IF EXISTS conversation_status;")
    op.execute("DROP TYPE IF EXISTS document_status;")
    op.execute("DROP TYPE IF EXISTS document_type;")
