"""
cleaning.py - Endpoints for cleaning product stock management
=============================================================

Routes in this file:
  POST /api/cleaning/use                — give out a cleaning product
  POST /api/cleaning/receive            — record a delivery
  GET  /api/cleaning/stock              — stock levels for ALL products
  GET  /api/cleaning/stock/{product}    — stock level for ONE product

THE SAME PATTERN AS CHARGERS:
Four distinct products (razor, brush, mr_min, label_remover) each tracked
separately. The route extracts the product type from the request and passes
it as 'subtype' into the service.

If you notice this looks almost identical to chargers.py — that's the point.
Commit 3 will extract the repeated loop into a shared service method.
"""

from fastapi import APIRouter

from app.models.Inventory import (
    CleaningProduct,
    CleaningReceivedRequest,
    CleaningUsedRequest,
    ItemCategory,
)
from app.services import stock_service

router = APIRouter(prefix="/api/cleaning", tags=["Cleaning Products"])


@router.post("/use")
def use_cleaning_product(request: CleaningUsedRequest):
    """
    Record a cleaning product given out.

    Requires product_type (razor, brush, mr_min, or label_remover).
    Returns 400 if there is not enough of that product in stock.
    """
    return stock_service.give_out(
        category=ItemCategory.CLEANING_PRODUCT,
        subtype=request.product_type,
        quantity=request.quantity,
        given_to=request.given_to,
        notes=request.notes,
    )


@router.post("/receive")
def receive_cleaning_products(request: CleaningReceivedRequest):
    """
    Record a cleaning product delivery arriving.

    Stock for the specified product type goes UP.
    """
    return stock_service.receive_stock(
        category=ItemCategory.CLEANING_PRODUCT,
        subtype=request.product_type,
        quantity=request.quantity,
        notes=request.notes,
    )


@router.get("/stock")
def get_all_cleaning_stock():
    """
    Current stock levels for all cleaning products.

    Returns a list — one entry per product. Same shape as chargers GET /stock.
    """
    return [
        stock_service.get_stock_level(ItemCategory.CLEANING_PRODUCT, CleaningProduct.RAZOR),
        stock_service.get_stock_level(ItemCategory.CLEANING_PRODUCT, CleaningProduct.BRUSH),
        stock_service.get_stock_level(ItemCategory.CLEANING_PRODUCT, CleaningProduct.MR_MIN),
        stock_service.get_stock_level(ItemCategory.CLEANING_PRODUCT, CleaningProduct.LABEL_REMOVER),
    ]


@router.get("/stock/{product_type}")
def get_cleaning_stock(product_type: CleaningProduct):
    """
    Current stock level for one cleaning product.

    Path: /api/cleaning/stock/razor  or  /api/cleaning/stock/mr_min  etc.
    FastAPI validates the path value against the CleaningProduct enum.
    """
    return stock_service.get_stock_level(ItemCategory.CLEANING_PRODUCT, product_type)
