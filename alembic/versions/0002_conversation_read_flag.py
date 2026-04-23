"""conversation read flag for admin unread badge

Revision ID: 0002_conversation_read
Revises: 0001_initial
Create Date: 2026-04-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0002_conversation_read'
down_revision: str | None = '0001_initial'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'conversations',
        sa.Column('read', sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column('conversations', 'read')
