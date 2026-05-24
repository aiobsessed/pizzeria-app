from fastapi import APIRouter

from .dashboard import router as _dashboard_router
from .orders import router as _orders_router

router = APIRouter(prefix="/courier", tags=["frontend-courier"])
router.include_router(_dashboard_router)
router.include_router(_orders_router)
