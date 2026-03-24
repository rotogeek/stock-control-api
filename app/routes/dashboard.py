"""
dashboard.py - The stock overview endpoint
==========================================

Route in this file:
  GET /api/stock/dashboard — all stock levels at a glance

WHY THIS EXISTS:
Without this endpoint, a stock controller checking stock has to hit
9 separate endpoints (till rolls, each charger type, each cleaning product,
SIM cards, stickers). That's impractical. This endpoint returns everything
in one shot.

This is a read-only aggregation endpoint — it doesn't change any data.
"""

from fastapi import APIRouter

from app.models.Inventory import DashboardResponse
from app.services import stock_service

router = APIRouter(prefix="/api/stock", tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard():
    """
    Return all stock levels across every category at a glance.

    Includes:
    - All counted stock items (till rolls, chargers, SIM cards, etc.)
    - Battery status counts for each charging stage
    - Total number of stock line items being tracked
    - Timestamp of when this snapshot was taken
    """
    return stock_service.get_dashboard()
