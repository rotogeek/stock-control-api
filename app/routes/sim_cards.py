"""
sim_cards.py - Endpoints for SIM card stock management
=======================================================

Routes in this file:
  POST /api/sim-cards/use     — give SIM cards to someone (stock goes down)
  POST /api/sim-cards/receive — record a delivery (stock goes up)
  GET  /api/sim-cards/stock   — current SIM card count

SIM cards are simple counters — no subtypes, same pattern as till rolls.
"""

from fastapi import APIRouter

from app.models.Inventory import ItemCategory, StockReceivedRequest, StockUsedRequest
from app.services import stock_service

router = APIRouter(prefix="/api/sim-cards", tags=["SIM Cards"])


@router.post("/use")
def use_sim_cards(request: StockUsedRequest):
    """
    Record SIM cards given out to someone.

    Stock level goes DOWN. Returns 400 if not enough in stock.
    """
    return stock_service.give_out(
        category=ItemCategory.SIM_CARD,
        quantity=request.quantity,
        given_to=request.given_to,
        notes=request.notes,
    )


@router.post("/receive")
def receive_sim_cards(request: StockReceivedRequest):
    """Record a SIM card delivery arriving. Stock level goes UP."""
    return stock_service.receive_stock(
        category=ItemCategory.SIM_CARD,
        quantity=request.quantity,
        notes=request.notes,
    )


@router.get("/stock")
def get_sim_card_stock():
    """Check current SIM card stock level."""
    return stock_service.get_stock_level(category=ItemCategory.SIM_CARD)
