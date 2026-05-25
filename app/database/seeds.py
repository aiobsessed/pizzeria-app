from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import DeliveryType, OrderStatus, PaymentMethod, PromoType
from app.core.security import hash_password
from app.models import Employee, Position
from app.models.address import Address
from app.models.category import Category
from app.models.client import Client
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.promo import Promo

# ─── Системные данные ─────────────────────────────────────────────────────────

_SYSTEM_POSITIONS = [
    {"name": "Администратор", "role": "admin"},
    {"name": "Курьер",        "role": "courier"},
]

_SEED_CATALOG = [
    {
        "category": {"name": "Пиццы", "slug": "pizza"},
        "products": [
            {
                "name": "Пицца Гавайская",
                "description": "Куриное филе, ананасы, томатный соус, моцарелла",
                "composition": "тесто, томатный соус, куриное филе, ананасы, моцарелла",
                "weight": 460,
                "price": Decimal("649.00"),
                "image_url": "/static/img/pizza_hawaii.webp",
            },
            {
                "name": "Пицца Четыре сыра",
                "description": "Моцарелла, пармезан, гауда и дорблю на сливочной основе",
                "composition": "тесто, сливочный соус, моцарелла, пармезан, гауда, дорблю",
                "weight": 470,
                "price": Decimal("799.00"),
                "image_url": "/static/img/pizza_four_cheese.webp",
            },
            {
                "name": "Пицца BBQ",
                "description": "Куриное филе, соус барбекю, красный лук, моцарелла",
                "composition": "тесто, соус BBQ, куриное филе, моцарелла, красный лук, болгарский перец",
                "weight": 500,
                "price": Decimal("749.00"),
                "image_url": "/static/img/pizza_bbq.webp",
            },
            {
                "name": "Пицца Пепперони",
                "description": "Острая пепперони, томатный соус, моцарелла",
                "composition": "тесто, томатный соус, моцарелла, пепперони",
                "weight": 480,
                "price": Decimal("699.00"),
                "image_url": "/static/img/pizza_pepperoni.webp",
            },
            {
                "name": "Пицца Маргарита",
                "description": "Томатный соус, моцарелла фиор ди латте, свежий базилик",
                "composition": "тесто, томатный соус, моцарелла, базилик, оливковое масло",
                "weight": 450,
                "price": Decimal("599.00"),
                "image_url": "/static/img/pizza_margarita.webp",
            },
        ],
    },
    {
        "category": {"name": "Бургеры", "slug": "burgers"},
        "products": [
            {
                "name": "Бургер Классик",
                "description": "Говяжья котлета, салат айсберг, томат, маринованный огурец, фирменный соус",
                "composition": "булочка бриошь, говяжья котлета 180г, салат, томат, огурец маринованный, соус",
                "weight": 280,
                "price": Decimal("399.00"),
                "image_url": "/static/img/burger_classic.webp",
            },
        ],
    },
    {
        "category": {"name": "Напитки", "slug": "drinks"},
        "products": [
            {
                "name": "Кола",
                "description": "Освежающий газированный напиток",
                "composition": "газированная вода, сахар, краситель, ароматизатор",
                "weight": 500,
                "price": Decimal("149.00"),
                "image_url": "/static/img/cola.webp",
            },
            {
                "name": "Сок апельсиновый",
                "description": "Натуральный апельсиновый сок прямого отжима",
                "composition": "апельсиновый сок 100%",
                "weight": 300,
                "price": Decimal("179.00"),
                "image_url": "/static/img/juice_orange.webp",
            },
        ],
    },
]

# ─── Демо-данные ──────────────────────────────────────────────────────────────
# Пароль для всех демо-аккаунтов: Demo1234!

_DEMO_CLIENTS = [
    {"name": "Алексей",   "email": "aleksey.smirnov@example.com",    "phone": "+79001234501"},
    {"name": "Мария",     "email": "maria.ivanova@example.com",      "phone": "+79001234502"},
    {"name": "Дмитрий",   "email": "dmitry.kozlov@example.com",      "phone": "+79001234503"},
    {"name": "Екатерина", "email": "ekaterina.novikova@example.com", "phone": "+79001234504"},
    {"name": "Сергей",    "email": "sergey.petrov@example.com",      "phone": "+79001234505"},
]

_DEMO_COURIERS = [
    {"name": "Иван Курьеров",    "email": "ivan.courier@example.com",    "phone": "+79002234501", "inn": "620100000001"},
    {"name": "Павел Быстров",    "email": "pavel.bystrov@example.com",   "phone": "+79002234502", "inn": "620100000002"},
    {"name": "Ольга Доставкина", "email": "olga.dostavkina@example.com", "phone": "+79002234503", "inn": "620100000003"},
    {"name": "Андрей Скоков",    "email": "andrey.skokov@example.com",   "phone": "+79002234504", "inn": "620100000004"},
    {"name": "Юлия Трекова",     "email": "yuliya.trekova@example.com",  "phone": "+79002234505", "inn": "620100000005"},
]

_DEMO_ADDRESSES = [
    {"client_email": "aleksey.smirnov@example.com",    "city": "Рязань", "street": "ул. Ленина",    "house": "15", "apartment": "42",  "comment": None},
    {"client_email": "aleksey.smirnov@example.com",    "city": "Рязань", "street": "ул. Советская", "house": "12", "apartment": "5",   "comment": "Код домофона 1234"},
    {"client_email": "maria.ivanova@example.com",      "city": "Рязань", "street": "ул. Пушкина",   "house": "8",  "apartment": None,  "comment": None},
    {"client_email": "dmitry.kozlov@example.com",      "city": "Рязань", "street": "пр. Победы",    "house": "23", "apartment": "101", "comment": None},
    {"client_email": "ekaterina.novikova@example.com", "city": "Рязань", "street": "ул. Есенина",   "house": "3",  "apartment": "15",  "comment": "3 этаж"},
    {"client_email": "sergey.petrov@example.com",      "city": "Рязань", "street": "ул. Гагарина",  "house": "50", "apartment": "7",   "comment": None},
]

_DEMO_PROMOS = [
    {
        "code": "WELCOME10",
        "promo_type": PromoType.order_discount,
        "discount_percent": Decimal("10.00"),
        "product_name": None,
        "max_usages": None,
        "first_order_only": False,
    },
    {
        "code": "NEWBIE20",
        "promo_type": PromoType.order_discount,
        "discount_percent": Decimal("20.00"),
        "product_name": None,
        "max_usages": None,
        "first_order_only": True,
    },
    {
        "code": "PIZZA20",
        "promo_type": PromoType.item_discount,
        "discount_percent": Decimal("20.00"),
        "product_name": "Пицца Маргарита",
        "max_usages": 50,
        "first_order_only": False,
    },
    {
        "code": "FREECOLA",
        "promo_type": PromoType.free_item,
        "discount_percent": None,
        "product_name": "Кола",
        "max_usages": 100,
        "first_order_only": False,
    },
    {
        "code": "SUMMER15",
        "promo_type": PromoType.order_discount,
        "discount_percent": Decimal("15.00"),
        "product_name": None,
        "max_usages": 100,
        "first_order_only": False,
    },
    {
        "code": "BURGER30",
        "promo_type": PromoType.item_discount,
        "discount_percent": Decimal("30.00"),
        "product_name": "Бургер Классик",
        "max_usages": 30,
        "first_order_only": False,
    },
]

# items: (product_name, quantity, price_at_order)
_DEMO_ORDERS = [
    {
        "client_email":  "aleksey.smirnov@example.com",
        "courier_email": "ivan.courier@example.com",
        "address_index": 0,
        "delivery_type":  DeliveryType.delivery,
        "payment_method": PaymentMethod.card,
        "status":   OrderStatus.delivered,
        "days_ago": 30,
        "items": [
            ("Пицца Гавайская", 1, Decimal("649.00")),
            ("Кола",            2, Decimal("149.00")),
        ],
    },
    {
        "client_email":  "maria.ivanova@example.com",
        "courier_email": None,
        "address_index": None,
        "delivery_type":  DeliveryType.pickup,
        "payment_method": PaymentMethod.cash,
        "status":   OrderStatus.delivered,
        "days_ago": 25,
        "items": [
            ("Бургер Классик",   2, Decimal("399.00")),
            ("Сок апельсиновый", 1, Decimal("179.00")),
        ],
    },
    {
        "client_email":  "dmitry.kozlov@example.com",
        "courier_email": "pavel.bystrov@example.com",
        "address_index": 0,
        "delivery_type":  DeliveryType.delivery,
        "payment_method": PaymentMethod.online,
        "status":   OrderStatus.delivered,
        "days_ago": 20,
        "items": [
            ("Пицца BBQ",       1, Decimal("749.00")),
            ("Пицца Пепперони", 1, Decimal("699.00")),
            ("Кола",            1, Decimal("149.00")),
        ],
    },
    {
        "client_email":  "ekaterina.novikova@example.com",
        "courier_email": "olga.dostavkina@example.com",
        "address_index": 0,
        "delivery_type":  DeliveryType.delivery,
        "payment_method": PaymentMethod.card,
        "status":   OrderStatus.on_the_way,
        "days_ago": 0,
        "items": [
            ("Пицца Четыре сыра", 2, Decimal("799.00")),
        ],
    },
    {
        "client_email":  "sergey.petrov@example.com",
        "courier_email": None,
        "address_index": None,
        "delivery_type":  DeliveryType.pickup,
        "payment_method": PaymentMethod.cash,
        "status":   OrderStatus.preparing,
        "days_ago": 0,
        "items": [
            ("Бургер Классик", 1, Decimal("399.00")),
            ("Кола",           2, Decimal("149.00")),
        ],
    },
    {
        "client_email":  "aleksey.smirnov@example.com",
        "courier_email": None,
        "address_index": None,
        "delivery_type":  DeliveryType.pickup,
        "payment_method": PaymentMethod.card,
        "status":   OrderStatus.canceled,
        "days_ago": 15,
        "items": [
            ("Пицца Маргарита", 1, Decimal("599.00")),
        ],
    },
    {
        "client_email":  "dmitry.kozlov@example.com",
        "courier_email": "andrey.skokov@example.com",
        "address_index": 0,
        "delivery_type":  DeliveryType.delivery,
        "payment_method": PaymentMethod.card,
        "status":   OrderStatus.accepted,
        "days_ago": 1,
        "items": [
            ("Пицца Маргарита",  1, Decimal("599.00")),
            ("Сок апельсиновый", 2, Decimal("179.00")),
        ],
    },
]


# ─── Публичные функции ────────────────────────────────────────────────────────

async def seed_defaults(session: AsyncSession) -> None:
    for pos_data in _SYSTEM_POSITIONS:
        exists = await session.scalar(select(Position).where(Position.name == pos_data["name"]))
        if exists is None:
            session.add(Position(**pos_data))
    await session.flush()

    for cat_position, entry in enumerate(_SEED_CATALOG):
        cat_data = entry["category"]
        category = await session.scalar(select(Category).where(Category.slug == cat_data["slug"]))
        if category is None:
            category = Category(**cat_data, is_active=False, position=cat_position)
            session.add(category)
            await session.flush()

        for prod_position, prod_data in enumerate(entry["products"]):
            exists = await session.scalar(select(Product).where(Product.name == prod_data["name"]))
            if exists is None:
                session.add(Product(
                    **prod_data,
                    category_id=category.id,
                    is_available=False,
                    position=prod_position,
                ))

    await session.commit()
    await seed_demo_data(session)


async def seed_demo_data(session: AsyncSession) -> None:
    if await session.scalar(select(Client).limit(1)) is not None:
        return

    now = datetime.now(timezone.utc)
    demo_password = hash_password("Demo1234!")

    clients: dict[str, Client] = {}
    for data in _DEMO_CLIENTS:
        client = Client(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            hashed_password=demo_password,
        )
        session.add(client)
        clients[data["email"]] = client
    await session.flush()

    client_addresses: dict[str, list[Address]] = {email: [] for email in clients}
    for addr in _DEMO_ADDRESSES:
        address = Address(
            client_id=clients[addr["client_email"]].id,
            city=addr["city"],
            street=addr["street"],
            house=addr["house"],
            apartment=addr["apartment"],
            comment=addr["comment"],
        )
        session.add(address)
        client_addresses[addr["client_email"]].append(address)
    await session.flush()

    courier_position = await session.scalar(select(Position).where(Position.name == "Курьер"))
    couriers: dict[str, Employee] = {}
    for data in _DEMO_COURIERS:
        courier = Employee(
            position_id=courier_position.id,
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            hashed_password=demo_password,
            inn=data["inn"],
        )
        session.add(courier)
        couriers[data["email"]] = courier
    await session.flush()

    product_names = (
        {item[0] for order in _DEMO_ORDERS for item in order["items"]}
        | {p["product_name"] for p in _DEMO_PROMOS if p["product_name"]}
    )
    products: dict[str, Product] = {}
    for name in product_names:
        product = await session.scalar(select(Product).where(Product.name == name))
        if product is not None:
            products[name] = product

    for promo in _DEMO_PROMOS:
        session.add(Promo(
            code=promo["code"],
            promo_type=promo["promo_type"],
            discount_percent=promo["discount_percent"],
            product_id=products[promo["product_name"]].id if promo["product_name"] else None,
            max_usages=promo["max_usages"],
            first_order_only=promo["first_order_only"],
        ))
    await session.flush()

    for order_def in _DEMO_ORDERS:
        addr_idx = order_def["address_index"]
        courier_email = order_def["courier_email"]
        client = clients[order_def["client_email"]]
        address = client_addresses[order_def["client_email"]][addr_idx] if addr_idx is not None else None
        courier = couriers.get(courier_email) if courier_email else None
        total_price = sum(
            (price * qty for _, qty, price in order_def["items"]),
            Decimal("0"),
        )

        order = Order(
            client_id=client.id,
            courier_id=courier.id if courier else None,
            address_id=address.id if address else None,
            delivery_type=order_def["delivery_type"],
            payment_method=order_def["payment_method"],
            status=order_def["status"],
            total_price=total_price,
            created_at=now - timedelta(days=order_def["days_ago"]),
        )
        session.add(order)
        await session.flush()

        for product_name, quantity, price_at_order in order_def["items"]:
            session.add(OrderItem(
                order_id=order.id,
                product_id=products[product_name].id,
                quantity=quantity,
                price_at_order=price_at_order,
            ))

    await session.commit()


async def check_admin_exists(session: AsyncSession) -> bool:
    admin_pos = await session.scalar(select(Position).where(Position.name == "Администратор"))
    if admin_pos is None:
        return False
    return await session.scalar(
        select(Employee).where(Employee.position_id == admin_pos.id).limit(1)
    ) is not None
