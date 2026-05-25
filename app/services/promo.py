from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PromoType
from app.core.exceptions import BusinessError, ConflictError, NotFoundError
from app.models.cart import CartItem
from app.models.order import Order
from app.models.promo import Promo
from app.repositories.promo import PromoRepository
from app.schemas.promo import PromoCreate, PromoPreview, PromoUpdate


class PromoService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.repo = PromoRepository(session)

    # ─── Admin ───────────────────────────────────────────────────────────────

    async def get_all(self) -> list[Promo]:
        promos = await self.repo.get_all_with_product()
        for promo in promos:
            if promo.is_active and self._is_stale(promo):
                await self._deactivate(promo)
        return promos

    async def get_by_id(self, promo_id: int) -> Promo:
        promo = await self.repo.get_by_id(promo_id)
        if promo is None:
            raise NotFoundError("Промокод не найден")
        return promo

    async def create(self, data: PromoCreate) -> Promo:
        if await self.repo.get_by_code(data.code):
            raise ConflictError("Промокод с таким кодом уже существует")
        return await self.repo.create(Promo(**data.model_dump()))

    async def update(self, promo_id: int, data: PromoUpdate) -> Promo:
        promo = await self.get_by_id(promo_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(promo, field, value)
        return await self.repo.update(promo)

    # ─── Client ──────────────────────────────────────────────────────────────

    async def preview(
        self, code: str, cart_items: list[CartItem], total: Decimal, client_id: int
    ) -> PromoPreview:
        promo = await self._get_applicable(code, client_id)
        return self._calculate_preview(promo, cart_items, total)

    async def apply(
        self, code: str, cart_items: list[CartItem], total: Decimal, client_id: int
    ) -> tuple[Promo, PromoPreview]:
        """Возвращает (promo, preview). Инкремент used_count — при сохранении заказа."""
        promo = await self._get_applicable(code, client_id)
        preview = self._calculate_preview(promo, cart_items, total)
        return promo, preview

    async def increment_usage(self, promo: Promo) -> None:
        promo.used_count += 1
        if promo.max_usages is not None and promo.used_count >= promo.max_usages:
            promo.is_active = False
        await self.repo.update(promo)

    # ─── Internal ────────────────────────────────────────────────────────────

    async def _get_applicable(self, code: str, client_id: int) -> Promo:
        promo = await self.repo.get_by_code(code)
        if promo is None or not promo.is_active:
            raise NotFoundError("Промокод не найден или неактивен")
        if promo.expires_at and promo.expires_at < datetime.now(timezone.utc):
            await self._deactivate(promo)
            raise BusinessError("Срок действия промокода истёк")
        if promo.max_usages is not None and promo.used_count >= promo.max_usages:
            await self._deactivate(promo)
            raise BusinessError("Промокод исчерпал лимит использований")
        if promo.first_order_only and await self._client_has_orders(client_id):
            raise BusinessError("Промокод доступен только для первого заказа")
        return promo

    def _is_stale(self, promo: Promo) -> bool:
        expired = bool(promo.expires_at and promo.expires_at < datetime.now(timezone.utc))
        exhausted = promo.max_usages is not None and promo.used_count >= promo.max_usages
        return expired or exhausted

    async def _deactivate(self, promo: Promo) -> None:
        promo.is_active = False
        await self.repo.update(promo)

    async def _client_has_orders(self, client_id: int) -> bool:
        count = await self._session.scalar(
            select(func.count()).select_from(Order).where(Order.client_id == client_id)
        )
        return (count or 0) > 0

    def _calculate_preview(
        self, promo: Promo, cart_items: list[CartItem], total: Decimal
    ) -> PromoPreview:
        discount = Decimal(0)
        free_product_name: str | None = None

        match promo.promo_type:
            case PromoType.order_discount:
                discount = (total * promo.discount_percent / 100).quantize(Decimal("0.01"))

            case PromoType.item_discount:
                for item in cart_items:
                    if item.product_id == promo.product_id:
                        item_total = item.product.price * item.quantity
                        discount = (item_total * promo.discount_percent / 100).quantize(Decimal("0.01"))
                        break
                if discount == 0:
                    raise BusinessError("Товар из промокода отсутствует в корзине")

            case PromoType.free_item:
                for item in cart_items:
                    if item.product_id == promo.product_id:
                        discount = item.product.price.quantize(Decimal("0.01"))
                        free_product_name = item.product.name
                        break
                if discount == 0:
                    raise BusinessError("Товар из промокода отсутствует в корзине")

        return PromoPreview(
            promo_id=promo.id,
            code=promo.code,
            promo_type=promo.promo_type,
            discount_amount=discount,
            total_after=max(total - discount, Decimal(0)),
            product_id=promo.product_id,
            free_product_name=free_product_name,
        )
