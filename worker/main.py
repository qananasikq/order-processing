import asyncio
import logging
import redis.asyncio as redis

from api.config import settings
from api.db import Order, SessionLocal
from api.log import setup_logging
from api.models import OrderStatus
from api.queue import pop_ready_order, promote_delayed_orders, schedule_order_retry
from logic.worker import decide_order_outcome

setup_logging()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('worker')
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


async def work(order_id: int) -> None:
    lock = f'order-lock:{order_id}'
    ok = await redis_client.set(lock, '1', ex=settings.lock_ttl_seconds, nx=True)
    if not ok:
        log.info(f'skip_locked id={order_id}')
        return

    try:
        async with SessionLocal() as session:
            order = await session.get(Order, order_id)
            if order is None:
                log.warning(f'order_missing id={order_id}')
                return

            if order.status not in [OrderStatus.QUEUED.value, OrderStatus.PROCESSING.value]:
                log.info(f'skip_order id={order_id} status={order.status}')
                return

            order.status = OrderStatus.PROCESSING.value
            order.error = None
            await session.commit()

            result = await process_order(order)
            await session.commit()
            log.info(f'order_processed id={order.id} status={order.status} tries={order.tries} result={result}')
    except Exception as exc:
        log.error(f'worker_unhandled_error id={order_id} error={exc}')
    finally:
        await redis_client.delete(lock)


async def process_order(order):
    await asyncio.sleep(0)
    decision = decide_order_outcome(order, max_retries=settings.max_retries)

    if decision.should_retry:
        order.tries += 1
        order.status = decision.status
        order.error = decision.error
        await schedule_order_retry(
            order.id,
            settings.retry_delay_seconds,
            reason=f'retry-{order.tries}',
        )
        return 'retry'

    if decision.status == OrderStatus.FAILED.value and decision.error:
        if 'retry budget exhausted' in decision.error:
            order.tries += 1

    order.status = decision.status
    order.error = decision.error
    return decision.status


async def consume() -> None:
    while True:
        await promote_delayed_orders()
        order_id = await pop_ready_order(timeout=5)
        if order_id is None:
            continue

        await work(order_id)


if __name__ == '__main__':
    asyncio.run(consume())
