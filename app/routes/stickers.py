"""
stickers.py - Endpoints for sticker stock management
=====================================================

Routes in this file:
  POST /api/stickers/use     — give stickers to someone (stock goes down)
  POST /api/stickers/receive — record a delivery (stock goes up)
  GET  /api/stickers/stock   — current sticker count

Stickers are simple counters — no subtypes, same pattern as till rolls.
They have the highest reorder threshold (20) because they're used very fast.
"""

from fastapi import APIRouter

from app.models.Inventory import ItemCategory, StockReceivedRequest, StockUsedRequest
from app.services import stock_service

router = APIRouter(prefix="/api/stickers", tags=["Stickers"])


@router.post("/use")
def use_stickers(request: StockUsedRequest):
    """
    Record stickers given out to someone.

    Stock level goes DOWN. Returns 400 if not enough in stock.
    """
    return stock_service.give_out(
        category=ItemCategory.STICKER,
        quantity=request.quantity,
        given_to=request.given_to,
        notes=request.notes,
    )


@router.post("/receive")
def receive_stickers(request: StockReceivedRequest):
    """Record a sticker delivery arriving. Stock level goes UP."""
    return stock_service.receive_stock(
        category=ItemCategory.STICKER,
        quantity=request.quantity,
        notes=request.notes,
    )


@router.get("/stock")
def get_sticker_stock():
    """Check current sticker stock level."""
    return stock_service.get_stock_level(category=ItemCategory.STICKER)
