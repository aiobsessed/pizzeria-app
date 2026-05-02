from .auth import router as auth_router
from .users import router as users_router
from .addresses import router as addresses_router
from .categories import router as categories_router
from .admin.categories import router as admin_categories_router
from .products import router as products_router
from .admin.products import router as admin_products_router
from .cart import router as cart_router

routers = [
    # public
    auth_router,
    users_router,
    addresses_router,
    categories_router,
    products_router,
    cart_router,
    # admin
    admin_categories_router,
    admin_products_router,
]
