"""
till_rolls.py - Endpoints for till roll stock management
=========================================================

Routes in this file:
  POST /api/till-rolls/use     — give till rolls to someone (stock goes down)
  POST /api/till-rolls/receive — record a delivery (stock goes up)
  GET  /api/till-rolls/stock   — check current till roll count

HOW THE LAYERS CONNECT:
  Request arrives → Route validates the shape of the data (Pydantic)
                  → Service enforces the business rules ("enough stock?")
                  → Storage reads/writes the data
                  → Route returns the result as JSON
"""

from fastapi import APIRouter

from app.models.Inventory import ItemCategory, StockReceivedRequest, StockUsedRequest
from app.services import stock_service

router = APIRouter(prefix="/api/till-rolls", tags=["Till Rolls"])


@router.post("/use")
def use_till_rolls(request: StockUsedRequest):
    """
    Record till rolls given out to someone.

    Stock level goes DOWN by the requested quantity.
    Returns 400 if there is not enough stock available.
    """
    return stock_service.give_out(
        category=ItemCategory.TILL_ROLL,
        quantity=request.quantity,
        given_to=request.given_to,
        notes=request.notes,
    )


@router.post("/receive")
def receive_till_rolls(request: StockReceivedRequest):
    """
    Record a till roll delivery arriving from the supplier.

    Stock level goes UP by the received quantity.
    """
    return stock_service.receive_stock(
        category=ItemCategory.TILL_ROLL,
        quantity=request.quantity,
        notes=request.notes,
    )


@router.get("/stock")
def get_till_roll_stock():
    """Check current till roll stock level and whether it is low."""
    return stock_service.get_stock_level(category=ItemCategory.TILL_ROLL)
