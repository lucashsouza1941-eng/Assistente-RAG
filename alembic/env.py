from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from src.db.base import Base
from src.modules.chat.models import Conversation, Message
from src.modules.knowledge.models import Document, DocumentChunk
from src.modules.settings.models import Setting

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    env_url = os.environ.get('DATABASE_URL', '').strip()
    if env_url:
        return env_url
    ini_url = config.get_main_option('sqlalchemy.url')
    if ini_url:
        return ini_url
    raise RuntimeError('Defina DATABASE_URL ou sqlalchemy.url em alembic.ini')


def run_migrations_offline() -> None:
    context.configure(url=_database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    ini_section = dict(config.get_section(config.config_ini_section, {}) or {})
    ini_section['sqlalchemy.url'] = _database_url()
    connectable = async_engine_from_config(ini_section, prefix='sqlalchemy.', poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_migrations_online())
