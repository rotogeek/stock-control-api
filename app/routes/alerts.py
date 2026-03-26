"""
alerts.py - Low-stock alert endpoint
=====================================

Route in this file:
  GET /api/alerts — items currently at or below their reorder threshold

WHY THIS IS USEFUL:
The stock controller checks this at the start of the day. If it's empty,
all stock is above threshold. If items appear here, an order needs placing.

This returns the CURRENT state — items that are low right now.
The alert event log (when items went low historically) is in the storage layer
and will be exposed in Phase 3 reporting.
"""

from fastapi import APIRouter

from app.models.Inventory import StockLevel
from app.services import stock_service

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("", response_model=list[StockLevel])
def get_alerts():
    """
    Return all stock items currently at or below their reorder level.

    Empty list means everything is adequately stocked.
    Items with reorder_level set to 0 are excluded (alerting disabled).
    """
    return stock_service.get_active_alerts()
