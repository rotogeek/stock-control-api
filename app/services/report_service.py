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
        report_date = date_type.fromisoformat(date_str)

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

    # --- usage_by_person ---
    # Group give-outs by recipient, then by (category, subtype)
    person_items: dict[str, dict[tuple, int]] = defaultdict(lambda: defaultdict(int))
    for t in day_transactions:
        if t["movement_type"] == MovementType.USED and t["given_to"]:
            key = (t["category"], t["subtype"])
            person_items[t["given_to"]][key] += t["quantity"]

    usage_by_person = [
        {
            "name": person,
            "items": [
                {"category": cat, "subtype": sub, "quantity": qty}
                for (cat, sub), qty in sorted(items.items(), key=lambda x: x[0])
            ],
        }
        for person, items in sorted(person_items.items())
    ]

    # --- low_stock_alerts ---
    low_stock_alerts = [
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
