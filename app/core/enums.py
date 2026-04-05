from enum import Enum


class Role(str, Enum):
    user = "user"
    admin = "admin"
    courier = "courier"


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
