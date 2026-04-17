"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-08 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_enum_if_missing(name: str, labels: tuple[str, ...]) -> None:
    """Evita falha ao reexecutar upgrade se o tipo já existir (ex.: migração interrompida)."""
    labels_sql = ', '.join(f"'{x}'" for x in labels)
    op.execute(
        f"""
        DO $$ BEGIN
            CREATE TYPE {name} AS ENUM ({labels_sql});
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    _create_enum_if_missing('document_type', ('PROCEDURE', 'FAQ', 'PROTOCOL', 'GENERAL'))
    _create_enum_if_missing('document_status', ('PENDING', 'PROCESSING', 'INDEXED', 'ERROR'))
    _create_enum_if_missing('conversation_status', ('ACTIVE', 'CLOSED', 'ESCALATED'))
    _create_enum_if_missing('message_role', ('USER', 'ASSISTANT', 'SYSTEM'))

    document_type_enum = postgresql.ENUM(
        'PROCEDURE', 'FAQ', 'PROTOCOL', 'GENERAL',
        name='document_type',
        create_type=False,
    )
    document_status_enum = postgresql.ENUM(
        'PENDING', 'PROCESSING', 'INDEXED', 'ERROR',
        name='document_status',
        create_type=False,
    )
    conversation_status_enum = postgresql.ENUM(
        'ACTIVE', 'CLOSED', 'ESCALATED',
        name='conversation_status',
        create_type=False,
    )
    message_role_enum = postgresql.ENUM(
        'USER', 'ASSISTANT', 'SYSTEM',
        name='message_role',
        create_type=False,
    )

    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('type', document_type_enum, nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('status', document_status_enum, nullable=False),
        sa.Column('chunks_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_hash'),
    )

    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('whatsapp_number_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.Enum(name='conversation_status', create_type=False), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_message_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('resolved_without_human', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', message_role_enum, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('key'),
    )

    op.execute(
        'CREATE INDEX ix_document_chunks_embedding_ivfflat '
        'ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);'
    )
    op.create_index('ix_conversations_whatsapp_number_hash', 'conversations', ['whatsapp_number_hash'])
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_documents_status', 'documents', ['status'])


def downgrade() -> None:
    op.drop_index('ix_documents_status', table_name='documents')
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_index('ix_conversations_whatsapp_number_hash', table_name='conversations')
    op.execute('DROP INDEX IF EXISTS ix_document_chunks_embedding_ivfflat;')

    op.drop_table('settings')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('document_chunks')
    op.drop_table('documents')

    op.execute('DROP TYPE IF EXISTS message_role;')
    op.execute('DROP TYPE IF EXISTS conversation_status;')
    op.execute('DROP TYPE IF EXISTS document_status;')
    op.execute('DROP TYPE IF EXISTS document_type;')
