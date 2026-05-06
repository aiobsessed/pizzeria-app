from enum import Enum


# ─── Роли и статусы сотрудников ──────────────────────────────────────────────
class EmployeeRole(str, Enum):
    admin = "admin"
    courier = "courier"


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
