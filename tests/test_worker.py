import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'

from api.db import Base, Order
from worker.main import work


@pytest.mark.asyncio
async def test_worker_marks_order_done(monkeypatch):
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    session_local = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_local() as session:
        order = Order(customer='u@example.com', items=[{'name': 'x', 'price': 50, 'qty': 1}], total=50)
        session.add(order)
        await session.commit()
        await session.refresh(order)
        order_id = order.id

    import worker.main as worker_main
    worker_main.SessionLocal = session_local

    class FakeRedis:
        async def set(self, *args, **kwargs):
            return True
        async def delete(self, *args, **kwargs):
            return 1

    worker_main.redis_client = FakeRedis()

    await work(order_id)

    async with session_local() as session:
        saved = await session.get(Order, order_id)
        assert saved.status == 'done'
        assert saved.tries == 0

    await engine.dispose()


@pytest.mark.asyncio
async def test_worker_marks_order_failed_after_three_tries():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    session_local = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_local() as session:
        order = Order(
            customer='u@example.com',
            items=[{'name': 'preorder-book', 'price': 50, 'qty': 1}],
            total=50,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        order_id = order.id

    import worker.main as worker_main
    worker_main.SessionLocal = session_local

    class FakeRedis:
        async def set(self, *args, **kwargs):
            return True
        async def delete(self, *args, **kwargs):
            return 1

    async def fake_push_back(*args, **kwargs):
        return None

    worker_main.redis_client = FakeRedis()
    worker_main.schedule_order_retry = fake_push_back

    for _ in range(3):
        await work(order_id)

    async with session_local() as session:
        saved = await session.get(Order, order_id)
        assert saved.status == 'failed'
        assert saved.tries == 3

    await engine.dispose()


@pytest.mark.asyncio
async def test_worker_routes_bulk_order_to_manual_review():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    session_local = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_local() as session:
        order = Order(
            customer='u@example.com',
            items=[{'name': 'fragile-vase', 'price': 100, 'qty': 10}],
            total=1000,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        order_id = order.id

    import worker.main as worker_main
    worker_main.SessionLocal = session_local

    class FakeRedis:
        async def set(self, *args, **kwargs):
            return True
        async def delete(self, *args, **kwargs):
            return 1

    worker_main.redis_client = FakeRedis()

    await work(order_id)

    async with session_local() as session:
        saved = await session.get(Order, order_id)
        assert saved.status == 'manual_review'
        assert saved.tries == 0

    await engine.dispose()
