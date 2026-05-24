from fastapi import APIRouter

from .categories import router as categories_router
from .clients import router as clients_router
from .dashboard import router as dashboard_router
from .employees import router as employees_router
from .orders import router as orders_router
from .products import router as products_router
from .promos import router as promos_router
from .reports import router as reports_router

router = APIRouter(prefix="/admin", tags=["frontend-admin"])

router.include_router(dashboard_router)
router.include_router(orders_router)
router.include_router(clients_router)
router.include_router(products_router)
router.include_router(categories_router)
router.include_router(employees_router)
router.include_router(reports_router)
router.include_router(promos_router)
