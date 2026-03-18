import os

os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['READY_QUEUE_NAME'] = 'orders-test:ready'
os.environ['DELAYED_QUEUE_NAME'] = 'orders-test:delayed'
os.environ['MAX_RETRIES'] = '3'
os.environ['RETRY_DELAY_SECONDS'] = '1'

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.db import Base, get_db
from api.main import app


@pytest.fixture
async def client():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    session_local = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_db():
        async with session_local() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async def fake_publish(_: int, **kwargs):
        return None

    import api.main as api_main
    api_main.enqueue_order = fake_publish

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
