"""
transactions.py - Transaction history endpoints
================================================

Every stock movement that has ever been recorded lives in the transaction
log. These endpoints let stock controllers query that history.

WHY TRANSACTION HISTORY MATTERS:
Without it you only know "till rolls: 45."
With it you know: Thabo got 3 at 9:15am, a delivery of 50 came at 2pm.
That history is what makes daily reports (Day 8) possible and trustworthy.

FILTERS (all optional, combinable):
  ?date=2026-03-25       — only movements on that day
  ?category=charger      — only one item type
  ?given_to=thabo        — case-insensitive name search
  ?page=1&per_page=20    — pagination (defaults shown)
"""

from fastapi import APIRouter, Query, Response
from app.models.Inventory import TransactionListResponse
from app.services import stock_service as service

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    response: Response,
    date: str | None = Query(
        default=None,
        description="Filter by date (YYYY-MM-DD). Returns all movements on that day.",
        example="2026-03-25",
    ),
    category: str | None = Query(
        default=None,
        description="Filter by item category (e.g. 'charger', 'till_roll', 'sim_card').",
        example="charger",
    ),
    given_to: str | None = Query(
        default=None,
        description="Filter by recipient name (case-insensitive, partial match).",
        example="thabo",
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Results per page (max 100)"),
):
    """
    List all stock movements with optional filters and pagination.

    Returns every give-out and delivery across all categories.
    Filters are combinable — e.g. ?category=charger&given_to=thabo&date=2026-03-25

    Pagination metadata is in both the response body and the X-Total-Count header.
    """
    result = service.get_transactions(
        date=date,
        category=category,
        given_to=given_to,
        page=page,
        per_page=per_page,
    )
    # Expose total record count in a header — standard REST pagination practice.
    # Clients can read this without parsing the body to know if there are more pages.
    response.headers["X-Total-Count"] = str(result["total"])
    return result
