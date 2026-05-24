from app.core.enums import OrderStatus
from app.models import Order

_TERMINAL_STATUSES = frozenset({OrderStatus.delivered, OrderStatus.canceled})


def active_orders(orders: list[Order]) -> list[Order]:
    return [o for o in orders if o.status not in _TERMINAL_STATUSES]
