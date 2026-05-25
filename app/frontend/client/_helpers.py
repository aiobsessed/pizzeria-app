import json
from decimal import Decimal

from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError, NotFoundError
from app.models import CartItem
from app.schemas.promo import PromoPreview
from app.services.promo import PromoService


def _htmx_flash(response: HTMLResponse, message: str, success: bool = False) -> HTMLResponse:
    response.headers["HX-Trigger"] = json.dumps(
        {"showflash": {"message": message, "success": success}}
    )
    return response


def _cart_unavailable_names(items: list[CartItem]) -> list[str]:
    return [
        item.product.name
        for item in items
        if not item.product.is_available or not item.product.category.is_active
    ]


async def _resolve_promo(
    code: str, items: list[CartItem], total: Decimal, session: AsyncSession, client_id: int
) -> tuple[PromoPreview | None, str | None]:
    normalized = code.strip().upper()
    if not normalized:
        return None, None
    try:
        preview = await PromoService(session).preview(normalized, items, total, client_id)
        return preview, normalized
    except (NotFoundError, BusinessError):
        return None, None
