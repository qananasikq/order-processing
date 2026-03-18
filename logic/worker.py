from __future__ import annotations

from dataclasses import dataclass

from api.db import Order
from api.models import OrderStatus


class RetryableFulfillmentError(Exception):
    pass


class TerminalFulfillmentError(Exception):
    pass


class ManualReviewRequired(Exception):
    pass


@dataclass(slots=True)
class ProcessingDecision:
    status: str
    error: str | None = None
    should_retry: bool = False


def _names(order: Order) -> set[str]:
    return {str(item.get('name', '')).lower() for item in order.items}


def _units(order: Order) -> int:
    return sum(int(item.get('qty', 0)) for item in order.items)


def _run_fulfillment_rules(order: Order) -> None:
    item_names = _names(order)
    units = _units(order)

    if order.total >= 3000 or units >= 25:
        raise ManualReviewRequired('bulk order requires operator review before packing')

    if any(name.startswith('fragile-') for name in item_names) and units >= 10:
        raise ManualReviewRequired('fragile batch must be reviewed by warehouse lead')

    if any(name.startswith('blocked-') for name in item_names):
        raise TerminalFulfillmentError('catalogue blocked one of the items')

    if any(name.startswith('preorder-') for name in item_names):
        raise RetryableFulfillmentError('supplier feed has not confirmed stock yet')


def decide_order_outcome(order: Order, *, max_retries: int) -> ProcessingDecision:
    try:
        _run_fulfillment_rules(order)
    except ManualReviewRequired as exc:
        return ProcessingDecision(status=OrderStatus.MANUAL_REVIEW.value, error=str(exc))
    except TerminalFulfillmentError as exc:
        return ProcessingDecision(status=OrderStatus.FAILED.value, error=str(exc))
    except RetryableFulfillmentError as exc:
        if order.tries + 1 >= max_retries:
            return ProcessingDecision(
                status=OrderStatus.FAILED.value,
                error=f'{exc}; retry budget exhausted',
            )
        return ProcessingDecision(
            status=OrderStatus.QUEUED.value,
            error=str(exc),
            should_retry=True,
        )

    return ProcessingDecision(status=OrderStatus.DONE.value, error=None)