"""
reports.py - Daily report endpoint
====================================

Generates an end-of-day summary: what was used, who received what,
what's left, and what's running low.

Defaults to today. Pass ?date= for historical reports.
"""

from fastapi import APIRouter, Query
from app.models.Inventory import DailyReportResponse, StockLevel
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/daily", response_model=DailyReportResponse)
def daily_report(
    date: str | None = Query(
        default=None,
        description="Report date (YYYY-MM-DD). Defaults to today.",
        example="2026-03-25",
    ),
):
    """
    Generate the daily stock report.

    Returns a full summary of all stock movements for the given date:
    - Totals at a glance (given out, received, categories used)
    - Per-item breakdown (used, received, remaining for each active item)
    - Per-person breakdown (what each recipient received)
    - Low-stock alerts (items currently at or below reorder level)
    """
    return report_service.generate_daily_report(date_str=date)


@router.get("/daily/low-stock", response_model=list[StockLevel])
def daily_low_stock():
    """
    Return only the low-stock warnings section of the daily report.

    Shortcut for stock controllers who just want to see what needs
    reordering without loading the full report. Computed live from
    current stock levels.
    """
    return report_service.get_low_stock_warnings()
