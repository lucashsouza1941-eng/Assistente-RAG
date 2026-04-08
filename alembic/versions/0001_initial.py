"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-08 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0001_initial'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')


def downgrade() -> None:
    op.execute('DROP EXTENSION IF EXISTS vector;')
