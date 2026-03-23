"""
chargers.py - Endpoints for charger stock management
=====================================================

Routes in this file:
  POST /api/chargers/use              — give chargers out (type required)
  POST /api/chargers/receive          — record a delivery (type required)
  GET  /api/chargers/stock            — current stock for ALL charger types
  GET  /api/chargers/stock/{type}     — current stock for ONE charger type

WHY SUBTYPES MATTER:
Type-C and Micro chargers are different products. You can't substitute one
for the other. So each type has its own stock level and reorder threshold.

The route captures the type from the request body (for POST) or the URL
path (for GET) and passes it as 'subtype' into the service layer.
"""

from fastapi import APIRouter

from app.models.Inventory import (
    ChargerReceivedRequest,
    ChargerType,
    ChargerUsedRequest,
    ItemCategory,
)
from app.services import stock_service

router = APIRouter(prefix="/api/chargers", tags=["Chargers"])


@router.post("/use")
def use_chargers(request: ChargerUsedRequest):
    """
    Record chargers given out to someone.

    Requires charger_type (type_c or micro) — each type is tracked separately.
    Returns 400 if there is not enough stock of that type.
    """
    return stock_service.give_out(
        category=ItemCategory.CHARGER,
        subtype=request.charger_type,
        quantity=request.quantity,
        given_to=request.given_to,
        notes=request.notes,
    )


@router.post("/receive")
def receive_chargers(request: ChargerReceivedRequest):
    """
    Record a charger delivery arriving.

    Requires charger_type — stock is added to that type only.
    """
    return stock_service.receive_stock(
        category=ItemCategory.CHARGER,
        subtype=request.charger_type,
        quantity=request.quantity,
        notes=request.notes,
    )


@router.get("/stock")
def get_all_charger_stock():
    """
    Current stock levels for all charger types.

    Returns a list — one entry per type. Useful for the dashboard.
    """
    return stock_service.get_stock_levels_for_subtypes(
        ItemCategory.CHARGER, list(ChargerType)
    )


@router.get("/stock/{charger_type}")
def get_charger_stock(charger_type: ChargerType):
    """
    Current stock level for one charger type.

    Path: /api/chargers/stock/type_c  or  /api/chargers/stock/micro
    FastAPI validates the path value against the ChargerType enum automatically.
    """
    return stock_service.get_stock_level(ItemCategory.CHARGER, charger_type)
