from __future__ import annotations

import os
from collections.abc import AsyncGenerator

# Bootstrap antes de importar `src.*` para alinhar DATABASE_URL/REDIS_URL ao stack de teste
# (AsyncSessionLocal e get_settings() usam essas variáveis ao carregar o módulo).
_DEFAULT_TEST_DB = 'postgresql+asyncpg://postgres:postgres@localhost:5433/test_odontobot'
_DEFAULT_TEST_REDIS = 'redis://localhost:6380/0'
_TEST_DB = os.getenv('TEST_DATABASE_URL', _DEFAULT_TEST_DB)
_TEST_REDIS = os.getenv('TEST_REDIS_URL', _DEFAULT_TEST_REDIS)
os.environ.setdefault('DATABASE_URL', _TEST_DB)
os.environ.setdefault('REDIS_URL', _TEST_REDIS)

TEST_DATABASE_URL = _TEST_DB
TEST_REDIS_URL = _TEST_REDIS

import pytest
import pytest_asyncio
from arq.connections import RedisSettings, create_pool
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.dependencies import get_arq_redis, get_db_session, get_redis, get_settings
from src.main import create_app


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


@pytest.fixture(autouse=True)
def mock_minio_storage(monkeypatch):
    storage: dict[str, bytes] = {}

    async def _ensure_bucket(self):
        return None

    async def _upload_bytes(self, object_name: str, content: bytes, content_type: str | None = None):
        storage[object_name] = content

    async def _download_bytes(self, object_name: str) -> bytes:
        if object_name not in storage:
            raise FileNotFoundError(object_name)
        return storage[object_name]

    async def _exists(self, object_name: str) -> bool:
        return object_name in storage

    monkeypatch.setattr('src.modules.knowledge.storage.MinioStorage.ensure_bucket', _ensure_bucket)
    monkeypatch.setattr('src.modules.knowledge.storage.MinioStorage.upload_bytes', _upload_bytes)
    monkeypatch.setattr('src.modules.knowledge.storage.MinioStorage.download_bytes', _download_bytes)
    monkeypatch.setattr('src.modules.knowledge.storage.MinioStorage.exists', _exists)


@pytest.fixture(autouse=True)
def mock_meta_api_factory(monkeypatch):
    async def _mk(_db, _settings):
        return _MetaAPIStub()

    # `from factory import create_meta_api_client` copia a referência; patch onde o nome é usado.
    for _target in (
        'src.modules.whatsapp.factory.create_meta_api_client',
        'src.modules.whatsapp.service.create_meta_api_client',
        'src.modules.whatsapp.admin_router.create_meta_api_client',
    ):
        monkeypatch.setattr(_target, _mk)


class _MetaAPIStub:
    async def aclose(self) -> None:
        return None

    async def fetch_phone_number_profile(self) -> dict:
        """Usado por GET /whatsapp/admin/connection — evita HTTP à Graph API nos testes."""
        return {
            'id': 'stub-phone-id',
            'verified_name': 'Clinica Stub',
            'display_phone_number': '+55 11 90000-0000',
            'quality_rating': 'GREEN',
            'messaging_limit_tier': 'TIER_1',
        }

    async def send_text_message(self, to: str, text: str):
        return None

    async def mark_as_read(self, message_id: str):
        return None


@pytest_asyncio.fixture
async def client(async_session: AsyncSession, redis_client: Redis, mock_openai) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    app.state.redis_client = redis_client

    async def _db_override():
        yield async_session

    async def _redis_override():
        return redis_client

    async def _arq_override():
        pool = await create_pool(RedisSettings.from_dsn(TEST_REDIS_URL))
        try:
            yield pool
        finally:
            await pool.close()

    app.dependency_overrides[get_db_session] = _db_override
    app.dependency_overrides[get_redis] = _redis_override
    app.dependency_overrides[get_arq_redis] = _arq_override

    headers = {'X-API-Key': get_settings().api_key}
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test', headers=headers) as ac:
        yield ac

    app.dependency_overrides.clear()
