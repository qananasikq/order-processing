from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import Order, get_db
from api.dto import NewOrderDto, OrderViewDto
from api.log import setup_logging
from api.models import OrderStatus
from api.queue import enqueue_order
from logic.orders import order_to_view, prepare_order

setup_logging()
app = FastAPI(title='order-service')


@app.get('/health')
async def health():
    return {'ok': True}


@app.post('/orders', response_model=OrderViewDto, status_code=201)
async def add_order(data: NewOrderDto, session: AsyncSession = Depends(get_db)):
    try:
        prepared_items, prepared_total = prepare_order(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    order = Order(
        customer=data.customer.strip().lower(),
        items=prepared_items,
        total=prepared_total,
        status=OrderStatus.QUEUED.value,
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)

    await enqueue_order(order.id, reason='new-order')
    return order_to_view(order)


@app.get('/orders/{order_id}', response_model=OrderViewDto)
async def get_order(order_id: int, session: AsyncSession = Depends(get_db)):
    order = await session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail='order not found')
    return order_to_view(order)
