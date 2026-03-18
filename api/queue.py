import json
import time

import redis.asyncio as redis

from api.config import settings

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def _payload(order_id: int, reason: str) -> str:
    return json.dumps({'order_id': order_id, 'reason': reason})


async def enqueue_order(order_id: int, *, reason: str = 'new') -> None:
    client = await get_redis()
    await client.rpush(settings.ready_queue_name, _payload(order_id, reason))


async def schedule_order_retry(order_id: int, delay_seconds: int, *, reason: str) -> None:
    client = await get_redis()
    run_at = time.time() + delay_seconds
    await client.zadd(settings.delayed_queue_name, {_payload(order_id, reason): run_at})


async def promote_delayed_orders(limit: int = 50) -> int:
    client = await get_redis()
    due = await client.zrangebyscore(settings.delayed_queue_name, min=0, max=time.time(), start=0, num=limit)
    if not due:
        return 0

    pipe = client.pipeline(transaction=True)
    for raw in due:
        pipe.rpush(settings.ready_queue_name, raw)
        pipe.zrem(settings.delayed_queue_name, raw)
    await pipe.execute()
    return len(due)


async def pop_ready_order(timeout: int = 5) -> int | None:
    client = await get_redis()
    data = await client.blpop(settings.ready_queue_name, timeout=timeout)
    if data is None:
        return None

    _, raw = data
    payload = json.loads(raw)
    return int(payload['order_id'])
