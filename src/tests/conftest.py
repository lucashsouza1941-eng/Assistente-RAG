from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.dependencies import get_db_session, get_redis, get_settings
from src.main import create_app

TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL', 'postgresql+asyncpg://user:pass@localhost:5432/test_odontobot')
TEST_REDIS_URL = os.getenv('TEST_REDIS_URL', 'redis://localhost:6380/0')


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[Redis, None]:
    client = Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
def mock_openai(monkeypatch):
    class _EmbItem:
        embedding = [0.1] * 1536

    class _EmbRes:
        data = [_EmbItem()]

    class _Embeddings:
        async def create(self, *args, **kwargs):
            return _EmbRes()

    class _OpenAI:
        embeddings = _Embeddings()

    monkeypatch.setattr('src.modules.knowledge.retriever.AsyncOpenAI', lambda api_key: _OpenAI())
    monkeypatch.setattr('src.modules.knowledge.indexer.AsyncOpenAI', lambda api_key: _OpenAI())


@pytest.fixture
def mock_meta_api(monkeypatch):
    class _Client:
        async def send_text_message(self, to: str, text: str):
            return None

        async def mark_as_read(self, message_id: str):
            return None

    monkeypatch.setattr('src.modules.whatsapp.service.MetaAPIClient', lambda settings: _Client())


@pytest_asyncio.fixture
async def client(async_session: AsyncSession, redis_client: Redis, mock_openai, mock_meta_api) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def _db_override():
        yield async_session

    async def _redis_override():
        yield redis_client

    app.dependency_overrides[get_db_session] = _db_override
    app.dependency_overrides[get_redis] = _redis_override

    headers = {'X-API-Key': get_settings().api_key}
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test', headers=headers) as ac:
        yield ac

    app.dependency_overrides.clear()
