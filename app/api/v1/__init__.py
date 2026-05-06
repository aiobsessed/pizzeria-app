from .auth import router as auth_router
from .clients import router as clients_router
from .addresses import router as addresses_router
from .categories import router as categories_router
from .products import router as products_router
from .cart import router as cart_router
from .orders import router as orders_router
from .couriers import router as couriers_router
from .admin import (
    admin_categories_router,
    admin_products_router,
    admin_orders_router,
    admin_couriers_router,
    admin_clients_router,
    admin_employees_router,
    admin_positions_router,
)

routers = [
    # public
    auth_router,
    clients_router,
    addresses_router,
    categories_router,
    products_router,
    cart_router,
    orders_router,
    couriers_router,
    # admin
    admin_categories_router,
    admin_products_router,
    admin_orders_router,
    admin_couriers_router,
    admin_clients_router,
    admin_employees_router,
    admin_positions_router,
]
