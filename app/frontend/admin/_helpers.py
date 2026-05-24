import asyncio
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EmployeeStatus, OrderStatus
from app.core.timezone import MSK
from app.services import EmployeeService, OrderService, PositionService


def _parse_enum(enum_cls, value: str | None):
    if not value:
        return None
    try:
        return enum_cls(value)
    except ValueError:
        return None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


async def _get_dashboard_context(session: AsyncSession) -> dict:
    today = datetime.now(MSK).date()

    today_orders, active_couriers, positions = await asyncio.gather(
        OrderService(session).get_all_with_items(date_from=today, date_to=today),
        EmployeeService(session).get_all(role="courier", status=EmployeeStatus.active),
        PositionService(session).get_all(),
    )

    courier_position = next((p for p in positions if p.role == "courier"), None)
    today_by_status  = {s: sum(1 for o in today_orders if o.status == s) for s in OrderStatus}
    today_revenue    = sum(o.total_price for o in today_orders if o.status == OrderStatus.delivered)
    in_progress      = sum(
        today_by_status[s]
        for s in (OrderStatus.accepted, OrderStatus.preparing, OrderStatus.on_the_way)
    )

    return {
        "today":                 today,
        "today_orders_count":    len(today_orders),
        "today_by_status":       today_by_status,
        "today_revenue":         today_revenue,
        "in_progress":           in_progress,
        "active_couriers_count": len(active_couriers),
        "courier_position_id":   courier_position.id if courier_position else None,
        "OrderStatus":           OrderStatus,
    }
