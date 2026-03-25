"""
report_service.py - Daily report generation
=============================================

Aggregates the transaction log into a human-readable end-of-day summary.

WHY A SEPARATE SERVICE:
Report logic is different from stock logic. stock_service answers
"can I give this out?" report_service answers "what happened today?"
Separating them keeps each service focused and easy to change independently.

THE REPORT BUILDS FROM TRANSACTIONS:
Every give-out and delivery was already recorded in the transaction log
(Day 7). The report just reads those records and groups them — by item,
by person, and by alert status.
"""

from collections import defaultdict
from datetime import date as date_type

from app.models.errors import StockAPIError
from app.models.Inventory import MovementType
from app.storage import memory as storage


def generate_daily_report(date_str: str | None = None) -> dict:
    """
    Generate the daily stock report for a given date.

    date_str: YYYY-MM-DD string. Defaults to today if not provided.

    Pulls all transactions for that day and groups them into:
      - summary: totals at a glance
      - usage_by_item: per-item give-out and receive counts + remaining stock
      - usage_by_person: what each person received (give-outs only)
      - low_stock_alerts: items currently at or below their reorder level
    """
    if date_str is None:
        report_date = date_type.today()
        date_str = report_date.isoformat()
    else:
        try:
            report_date = date_type.fromisoformat(date_str)
        except ValueError:
            raise StockAPIError(
                error="invalid_date",
                detail=f"Invalid date format: '{date_str}'. Use YYYY-MM-DD (e.g. 2026-03-25).",
            )

    all_transactions = storage.get_transactions()
    day_transactions = [
        t for t in all_transactions
        if t["created_at"].date() == report_date
    ]

    # --- usage_by_item ---
    # Accumulate quantities by (category, subtype) key
    item_used: dict[tuple, int] = defaultdict(int)
    item_received: dict[tuple, int] = defaultdict(int)

    for t in day_transactions:
        key = (t["category"], t["subtype"])
        if t["movement_type"] == MovementType.USED:
            item_used[key] += t["quantity"]
        elif t["movement_type"] == MovementType.RECEIVED:
            item_received[key] += t["quantity"]

    # Walk every known stock item and include the ones that had activity today
    all_stock = storage.get_all_stock()
    usage_by_item = []
    for item in all_stock:
        key = (item["category"], item["subtype"])
        used = item_used.get(key, 0)
        received = item_received.get(key, 0)
        if used > 0 or received > 0:
            usage_by_item.append({
                "category": item["category"],
                "subtype": item["subtype"],
                "used_today": used,
                "received_today": received,
                "remaining": item["quantity"],
            })

    # --- summary ---
    total_given_out = sum(item_used.values())
    total_received = sum(item_received.values())
    categories_used = len({cat for (cat, _) in item_used if item_used[(cat, _)] > 0})

    usage_by_person = _build_person_breakdown(day_transactions)
    low_stock_alerts = _build_low_stock_alerts(all_stock)

    return {
        "date": date_str,
        "summary": {
            "total_items_given_out": total_given_out,
            "total_items_received": total_received,
            "categories_used": categories_used,
        },
        "usage_by_item": usage_by_item,
        "usage_by_person": usage_by_person,
        "low_stock_alerts": low_stock_alerts,
    }


def get_low_stock_warnings() -> list[dict]:
    """
    Return items currently at or below their reorder level.

    Used by GET /api/reports/daily/low-stock — same data as the
    low_stock_alerts section of the full daily report, exposed
    as a standalone endpoint for quick checks.
    """
    return _build_low_stock_alerts(storage.get_all_stock())


def _build_person_breakdown(day_transactions: list[dict]) -> list[dict]:
    """
    Group give-outs by recipient.

    Returns one entry per person, each containing a list of items they
    received today. Sorted alphabetically by name for consistent output.

    Only give-outs (movement_type=used) are included — deliveries have no
    recipient so they don't belong in the per-person view.
    """
    person_items: dict[str, dict[tuple, int]] = defaultdict(lambda: defaultdict(int))
    for t in day_transactions:
        if t["movement_type"] == MovementType.USED and t["given_to"]:
            key = (t["category"], t["subtype"])
            person_items[t["given_to"]][key] += t["quantity"]

    return [
        {
            "name": person,
            "items": [
                {"category": cat, "subtype": sub, "quantity": qty}
                for (cat, sub), qty in sorted(items.items(), key=lambda x: x[0])
            ],
        }
        for person, items in sorted(person_items.items())
    ]


def _build_low_stock_alerts(all_stock: list[dict]) -> list[dict]:
    """
    Return all items currently at or below their reorder level.

    Computed from live stock — not from the alert event log. This answers
    "what is low right now?" rather than "when did it go low?"

    Items with reorder_level=0 are excluded (alerting disabled for them).
    """
    return [
        {
            "category": item["category"],
            "subtype": item["subtype"],
            "current_quantity": item["quantity"],
            "reorder_level": item["reorder_level"],
            "is_low": True,
            "last_updated": item["last_updated"],
        }
        for item in all_stock
        if item["reorder_level"] > 0 and item["quantity"] <= item["reorder_level"]
    ]
