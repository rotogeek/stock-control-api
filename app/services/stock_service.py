"""
stock_service.py - Business rules for stock movements
======================================================

THE SEPARATION OF CONCERNS:
Routes handle HTTP (request in, response out).
Storage handles data (reads and writes to the store).
This service layer handles BUSINESS RULES — the "what is allowed" logic:
  - "You can't give out more than you have in stock."
  - "Clean up whitespace in names before saving."
  - "If stock drops below reorder level, flag it."

This is where the actual thinking happens. If a business rule changes
(e.g. "allow small overdrafts for managers"), you change it HERE only.
"""

from datetime import datetime

from app.models.errors import StockAPIError
from app.models.Inventory import ItemCategory, MovementType
from app.storage import memory as storage


def give_out(
    category: str,
    quantity: int,
    given_to: str,
    notes: str = "",
    subtype: str = "",
    recorded_by: str = "stock_controller",
) -> dict:
    """
    Give out stock to a person. Stock level goes DOWN.

    Business rules enforced here:
    - Cannot give out more than is currently in stock.
    - given_to is trimmed so "  Thabo  " and "Thabo" match in reports.
    """
    given_to = given_to.strip()
    notes = notes.strip()

    current = storage.get_stock(category, subtype)

    if quantity > current:
        item_name = category.replace("_", " ")
        if subtype:
            item_name = f"{subtype.replace('_', ' ')} {item_name}"
        raise StockAPIError(
            error="insufficient_stock",
            detail=(
                f"Cannot give out {quantity} {item_name}(s). "
                f"Only {current} currently in stock."
            ),
        )

    new_quantity = storage.subtract_stock(category, subtype, quantity)

    reorder_level = storage.get_reorder_level(category, subtype)
    if reorder_level > 0 and new_quantity <= reorder_level:
        storage.save_alert(category, subtype, new_quantity, reorder_level)

    return storage.save_transaction(
        category=category,
        subtype=subtype,
        movement_type=MovementType.USED,
        quantity=quantity,
        given_to=given_to,
        notes=notes,
        recorded_by=recorded_by,
    )


def receive_stock(
    category: str,
    quantity: int,
    notes: str = "",
    subtype: str = "",
    recorded_by: str = "stock_controller",
) -> dict:
    """
    Record a delivery arriving. Stock level goes UP.

    No upper-limit check — a large delivery is always valid.
    """
    notes = notes.strip()

    storage.add_stock(category, subtype, quantity)

    return storage.save_transaction(
        category=category,
        subtype=subtype,
        movement_type=MovementType.RECEIVED,
        quantity=quantity,
        given_to="",
        notes=notes,
        recorded_by=recorded_by,
    )


def get_stock_level(category: str, subtype: str = "") -> dict:
    """Return current stock level and metadata for one item."""
    record = storage.get_stock_record(category, subtype)
    reorder_level = storage.get_reorder_level(category, subtype)
    return {
        "category": category,
        "subtype": subtype,
        "current_quantity": record["quantity"],
        "reorder_level": reorder_level,
        "is_low": record["quantity"] <= reorder_level,
        "last_updated": record["last_updated"],
    }


def take_device(
    serial_number: str,
    model: str,
    given_to: str,
    notes: str = "",
    recorded_by: str = "stock_controller",
) -> dict:
    """
    Record a device taken from own stock.

    Devices are unique items — we track the serial number, not a count.
    This is different from give_out: there's no "how many left" check.
    Instead we check that the same serial number isn't logged twice.

    Business rule: each serial number can only be taken once.
    If you try to log the same device again, it fails with 400.
    """
    serial_number = serial_number.strip()
    given_to = given_to.strip()
    notes = notes.strip()

    if storage.device_already_taken(serial_number):
        raise StockAPIError(
            error="duplicate_serial",
            detail=f"Device {serial_number} has already been logged as taken.",
        )

    result = storage.save_device_transaction(
        serial_number=serial_number,
        model=model.strip(),
        given_to=given_to,
        notes=notes,
        recorded_by=recorded_by,
    )

    # Also record in the unified transaction log so device take-outs appear
    # alongside all other movements when querying /api/transactions.
    tx_notes = f"Serial: {serial_number} | Model: {model.strip()}"
    if notes:
        tx_notes += f" | {notes}"
    storage.save_transaction(
        category=ItemCategory.OWN_STOCK_DEVICE,
        subtype="",
        movement_type=MovementType.USED,
        quantity=1,
        given_to=given_to,
        notes=tx_notes,
        recorded_by=recorded_by,
    )

    return result


def get_device_log() -> list[dict]:
    """Return all recorded device transactions."""
    return storage.get_device_log()


def update_battery_status(
    status: str,
    quantity: int,
    notes: str = "",
    recorded_by: str = "stock_controller",
) -> dict:
    """
    Set how many batteries are in a given charging stage.

    This is a SET, not an add. "10 batteries charging" means the count
    IS 10 now — not that 10 more were added. This reflects physical reality:
    you look at the rack and count what's there.

    All three stages are independent — updating "charging" doesn't affect
    "ready" or "in_use".
    """
    notes = notes.strip()
    storage.set_battery_level(status, quantity)
    return storage.save_battery_update(
        status=status,
        quantity=quantity,
        notes=notes,
        recorded_by=recorded_by,
    )


def get_battery_levels() -> list[dict]:
    """Return current counts for all three battery stages."""
    return storage.get_all_battery_levels()


def get_dashboard() -> dict:
    """
    Aggregate all stock levels into a single dashboard view.

    Pulls every entry from the stock store, enriches each with its reorder
    level and is_low flag, and returns them alongside a total count and a
    timestamp showing when this snapshot was taken.

    WHY A SEPARATE FUNCTION:
    The route shouldn't know about storage. The service owns the aggregation
    logic so the route stays thin: call service, return result.
    """
    all_stock = storage.get_all_stock()

    stock_levels = [
        {
            "category": item["category"],
            "subtype": item["subtype"],
            "current_quantity": item["quantity"],
            "reorder_level": item["reorder_level"],
            "is_low": item["quantity"] <= item["reorder_level"],
            "last_updated": item["last_updated"],
        }
        for item in all_stock
    ]

    total_units = sum(item["current_quantity"] for item in stock_levels)
    low_count = sum(1 for item in stock_levels if item["is_low"])

    batteries = [
        {
            "status": b["status"],
            "quantity": b["quantity"],
            "last_updated": b["last_updated"],
        }
        for b in storage.get_all_battery_levels()
    ]

    low_stock_alerts = [item for item in stock_levels if item["is_low"] and item["reorder_level"] > 0]

    return {
        "stock_levels": stock_levels,
        "batteries": batteries,
        "low_stock_alerts": low_stock_alerts,
        "total_items_tracked": len(stock_levels),
        "total_units_in_stock": total_units,
        "low_stock_count": low_count,
        "last_checked": datetime.now(),
    }


def get_active_alerts() -> list[dict]:
    """
    Return all stock items currently at or below their reorder level.

    Computed live from current stock — not from the alert log. The alert log
    records WHEN an item went low. This function answers: what is low RIGHT NOW?

    Only items with a reorder_level > 0 are included. A level of 0 means
    alerting is disabled for that item.
    """
    return [
        item for item in [get_stock_level(entry["category"], entry["subtype"])
                          for entry in storage.get_all_stock()]
        if item["reorder_level"] > 0 and item["is_low"]
    ]


def get_all_reorder_levels() -> list[dict]:
    """Return all configured reorder thresholds."""
    return storage.get_all_reorder_levels()


def update_reorder_level(category: str, subtype: str, level: int) -> dict:
    """
    Set the reorder threshold for one stock item.

    When stock drops to or below this number after a give-out, an alert fires.
    Setting level to 0 effectively disables alerting for that item.
    """
    valid_categories = {item.value for item in ItemCategory}
    if category not in valid_categories:
        raise StockAPIError(
            error="invalid_category",
            detail=f"Unknown category: '{category}'. Valid values: {sorted(valid_categories)}.",
        )
    storage.set_reorder_level(category, subtype, level)
    return {
        "category": category,
        "subtype": subtype,
        "reorder_level": level,
    }


def get_transactions(
    date: str | None = None,
    category: str | None = None,
    given_to: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """
    Return a filtered, paginated list of stock movements.

    Filters applied in order: date → category → given_to.
    Pagination is applied last, after all filtering.

    date format: YYYY-MM-DD — matches on created_at date only (not time).
    category: must match an ItemCategory value exactly (e.g. "charger").
    given_to: case-insensitive substring match so "thabo" finds "Thabo".
    """
    transactions = storage.get_transactions()

    if date:
        from datetime import date as date_type
        try:
            filter_date = date_type.fromisoformat(date)
        except ValueError:
            raise StockAPIError(
                error="invalid_date",
                detail=f"Invalid date format: '{date}'. Use YYYY-MM-DD (e.g. 2026-03-25).",
            )
        transactions = [t for t in transactions if t["created_at"].date() == filter_date]

    if category:
        valid_categories = {item.value for item in ItemCategory}
        if category not in valid_categories:
            raise StockAPIError(
                error="invalid_category",
                detail=f"Unknown category: '{category}'. Valid values: {sorted(valid_categories)}.",
            )
        transactions = [t for t in transactions if t["category"] == category]

    if given_to:
        needle = given_to.strip().lower()
        transactions = [t for t in transactions if needle in t["given_to"].lower()]

    total = len(transactions)
    pages = max(1, -(-total // per_page))  # Ceiling division
    offset = (page - 1) * per_page
    page_slice = transactions[offset: offset + per_page]

    return {
        "transactions": page_slice,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


def get_stock_levels_for_subtypes(category: str, subtypes: list) -> list[dict]:
    """
    Return stock levels for every subtype in a category.

    Used by routes that need to show all variants at once — all charger types,
    all cleaning products, etc. Keeps route files free of repeated loops.

    Before this existed, chargers.py and cleaning.py each listed every subtype
    manually. Same pattern, different values. DRY: one function, used in both.
    """
    return [get_stock_level(category, subtype) for subtype in subtypes]
