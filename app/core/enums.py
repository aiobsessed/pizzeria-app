from enum import Enum


# ─── Статусы сотрудников ─────────────────────────────────────────────────────
class EmployeeStatus(str, Enum):
    active = "active"
    fired = "fired"
    on_leave = "on_leave"


# ─── Заказы ──────────────────────────────────────────────────────────────────
class DeliveryType(str, Enum):
    delivery = "delivery"
    pickup = "pickup"


class PaymentMethod(str, Enum):
    cash = "cash"
    card = "card"
    online = "online"


class OrderStatus(str, Enum):
    accepted = "accepted"
    preparing = "preparing"
    on_the_way = "on_the_way"
    delivered = "delivered"
    canceled = "canceled"


# ─── Промокоды ───────────────────────────────────────────────────────────────
class PromoType(str, Enum):
    free_item = "free_item"        # бесплатный товар
    item_discount = "item_discount"  # скидка на конкретный товар в корзине
    order_discount = "order_discount"  # скидка на весь заказ
