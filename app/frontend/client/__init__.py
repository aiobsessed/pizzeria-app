from fastapi import APIRouter

from .cart import router as cart_router
from .index import router as index_router
from .orders import router as orders_router
from .profile import router as profile_router

router = APIRouter(tags=["frontend-client"])
router.include_router(index_router)
router.include_router(cart_router)
router.include_router(orders_router)
router.include_router(profile_router)
