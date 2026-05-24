from .auth import router as auth_router
from .client import router as client_router
from .admin import router as admin_router
from .courier import router as courier_router

routers = [auth_router, client_router, admin_router, courier_router]
