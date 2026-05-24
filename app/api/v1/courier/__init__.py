from fastapi import APIRouter

from .orders import router as _orders_router

courier_router = APIRouter(prefix="/courier", tags=["courier"])
courier_router.include_router(_orders_router)
