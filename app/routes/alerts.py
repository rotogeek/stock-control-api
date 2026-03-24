"""
alerts.py - Low-stock alert endpoint
=====================================

Route in this file:
  GET /api/alerts — items currently at or below their reorder threshold

WHY THIS IS USEFUL:
The stock controller checks this at the start of the day. If it's empty,
all stock is above threshold. If items appear here, an order needs placing.

This returns the CURRENT state — items that are low right now.
For a history of when items went low, see the alert log (future endpoint).
"""

from fastapi import APIRouter

from app.models.Inventory import StockLevel
from app.services import stock_service

router = APIRouter(prefix="/api", tags=["Alerts"])


@router.get("/alerts", response_model=list[StockLevel])
def get_alerts():
    """
    Return all stock items currently at or below their reorder level.

    Empty list means everything is adequately stocked.
    Items with reorder_level set to 0 are excluded (alerting disabled).
    """
    return stock_service.get_active_alerts()
