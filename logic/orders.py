from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from api.db import Order
from api.dto import NewOrderDto

MONEY_STEP = Decimal('0.01')
TOTAL_TOLERANCE = Decimal('0.01')
MAX_LINES = 20
MAX_LINE_QTY = 50


def _money(value: float | int | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_STEP, rounding=ROUND_HALF_UP)


def _normalize_name(name: str) -> str:
    return ' '.join(name.strip().lower().split())


def prepare_order(data: NewOrderDto) -> tuple[list[dict[str, float | int | str]], float]:
    if not data.items:
        raise ValueError('order must contain at least one line')

    merged: dict[str, dict[str, float | int | str]] = {}
    for item in data.items:
        normalized_name = _normalize_name(item.name)
        if not normalized_name:
            raise ValueError('item name must not be blank')
        if item.qty > MAX_LINE_QTY:
            raise ValueError('single line qty is above intake limit')

        bucket = merged.setdefault(
            normalized_name,
            {'name': normalized_name, 'price': float(_money(item.price)), 'qty': 0},
        )

        price = float(_money(item.price))
        if bucket['price'] != price:
            raise ValueError(f'line {normalized_name} has conflicting prices')
        bucket['qty'] += item.qty

    lines = list(merged.values())
    if len(lines) > MAX_LINES:
        raise ValueError('order is too fragmented for automatic intake')

    calculated_total = sum(_money(line['price']) * line['qty'] for line in lines)
    declared_total = _money(data.total)
    if abs(calculated_total - declared_total) > TOTAL_TOLERANCE:
        raise ValueError('declared total does not match line totals')

    return lines, float(calculated_total)


def order_to_view(order: Order) -> dict:
    return {
        'id': order.id,
        'customer': order.customer,
        'items': order.items,
        'total': order.total,
        'status': order.status,
        'tries': order.tries,
        'error': order.error,
        'created_at': order.created_at,
        'updated_at': order.updated_at,
    }