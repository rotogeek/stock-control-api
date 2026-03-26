"""
settings.py - Reorder level configuration endpoints
=====================================================

Routes in this file:
  GET /api/settings/reorder-levels               — view all thresholds
  PUT /api/settings/reorder-levels/{category}    — update one threshold

WHAT REORDER LEVELS DO:
When stock drops to or below the threshold after a give-out, the item
appears in GET /api/alerts. Each item has its own threshold because
you burn through stickers faster than you use label remover.

SUBTYPE HANDLING:
Items with subtypes (chargers, cleaning products) need the subtype
passed as a query parameter:
  PUT /api/settings/reorder-levels/charger?subtype=type_c
  PUT /api/settings/reorder-levels/cleaning_product?subtype=razor
Simple items (till rolls, SIM cards, stickers) use no subtype:
  PUT /api/settings/reorder-levels/till_roll
"""

from fastapi import APIRouter, Query

from app.models.Inventory import ReorderLevelUpdate
from app.services import stock_service

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("/reorder-levels")
def get_reorder_levels():
    """View the reorder threshold for every stock item."""
    return stock_service.get_all_reorder_levels()


@router.put("/reorder-levels/{category}")
def update_reorder_level(
    category: str,
    request: ReorderLevelUpdate,
    subtype: str = Query(default="", description="Required for chargers and cleaning products"),
):
    """
    Set the reorder threshold for one stock item.

    When stock drops to or below this number, the item appears in GET /api/alerts.
    Use subtype= for items with variants: ?subtype=type_c, ?subtype=razor, etc.
    Set reorder_level to 0 to disable alerting for that item.
    """
    return stock_service.update_reorder_level(category, subtype, request.reorder_level)
