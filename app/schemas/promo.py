from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.enums import PromoType


class PromoBase(BaseModel):
    code: str
    promo_type: PromoType
    discount_percent: Decimal | None = None
    product_id: int | None = None
    max_usages: int | None = None
    expires_at: datetime | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_fields_for_type(self) -> "PromoBase":
        match self.promo_type:
            case PromoType.free_item:
                if self.product_id is None:
                    raise ValueError("free_item требует product_id")
                if self.discount_percent is not None:
                    raise ValueError("free_item не использует discount_percent")
            case PromoType.item_discount:
                if self.product_id is None:
                    raise ValueError("item_discount требует product_id")
                if self.discount_percent is None:
                    raise ValueError("item_discount требует discount_percent")
            case PromoType.order_discount:
                if self.product_id is not None:
                    raise ValueError("order_discount не использует product_id")
                if self.discount_percent is None:
                    raise ValueError("order_discount требует discount_percent")
        return self

    @field_validator("discount_percent")
    @classmethod
    def validate_percent(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and not (0 < v <= 100):
            raise ValueError("discount_percent должен быть в диапазоне (0, 100]")
        return v

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class PromoCreate(PromoBase):
    pass


class PromoUpdate(BaseModel):
    is_active: bool | None = None
    max_usages: int | None = None
    expires_at: datetime | None = None


class PromoRead(PromoBase):
    id: int
    used_count: int

    model_config = ConfigDict(from_attributes=True)


# ─── Ответ на применение промокода (preview в корзине) ───────────────────────

class PromoPreview(BaseModel):
    promo_id: int
    code: str
    promo_type: PromoType
    discount_amount: Decimal
    total_after: Decimal
    product_id: int | None = None       # для item_discount и free_item — id целевого товара
    free_product_name: str | None = None  # для free_item

    model_config = ConfigDict(from_attributes=True)
