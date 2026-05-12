from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Employee, Position
from app.models.category import Category
from app.models.product import Product

_SYSTEM_POSITIONS = [
    {"name": "Администратор", "role": "admin"},
    {"name": "Курьер",        "role": "courier"},
]

_SEED_CATALOG = [
    {
        "category": {"name": "Пиццы", "slug": "pizza"},
        "products": [
            {
                "name": "Пицца Маргарита",
                "description": "Томатный соус, моцарелла фиор ди латте, свежий базилик",
                "composition": "тесто, томатный соус, моцарелла, базилик, оливковое масло",
                "weight": 450,
                "price": Decimal("599.00"),
                "image_url": "/static/img/pizza_margarita.webp",
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
                "name": "Пицца BBQ",
                "description": "Говяжья начинка, соус барбекю, красный лук, моцарелла",
                "composition": "тесто, соус BBQ, говядина, моцарелла, красный лук, болгарский перец",
                "weight": 500,
                "price": Decimal("749.00"),
                "image_url": "/static/img/pizza_bbq.webp",
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
                "name": "Пицца Гавайская",
                "description": "Куриное филе, ананасы, томатный соус, моцарелла",
                "composition": "тесто, томатный соус, куриное филе, ананасы, моцарелла",
                "weight": 460,
                "price": Decimal("649.00"),
                "image_url": "/static/img/pizza_hawaii.webp",
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


async def seed_defaults(session: AsyncSession) -> None:
    for pos_data in _SYSTEM_POSITIONS:
        exists = await session.scalar(select(Position).where(Position.name == pos_data["name"]))
        if exists is None:
            session.add(Position(**pos_data))
    await session.flush()

    for entry in _SEED_CATALOG:
        cat_data = entry["category"]
        category = await session.scalar(select(Category).where(Category.slug == cat_data["slug"]))
        if category is None:
            category = Category(**cat_data, is_active=False)
            session.add(category)
            await session.flush()

        for prod_data in entry["products"]:
            exists = await session.scalar(select(Product).where(Product.name == prod_data["name"]))
            if exists is None:
                session.add(Product(**prod_data, category_id=category.id, is_available=False))

    await session.commit()


async def check_admin_exists(session: AsyncSession) -> bool:
    admin_pos = await session.scalar(select(Position).where(Position.name == "Администратор"))
    if admin_pos is None:
        return False
    return await session.scalar(
        select(Employee).where(Employee.position_id == admin_pos.id).limit(1)
    ) is not None
