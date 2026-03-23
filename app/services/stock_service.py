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

from fastapi import HTTPException

from app.models.Inventory import MovementType
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
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot give out {quantity} {category.replace('_', ' ')}(s). "
                f"Only {current} currently in stock."
            ),
        )

    storage.subtract_stock(category, subtype, quantity)

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


def get_stock_levels_for_subtypes(category: str, subtypes: list) -> list[dict]:
    """
    Return stock levels for every subtype in a category.

    Used by routes that need to show all variants at once — all charger types,
    all cleaning products, etc. Keeps route files free of repeated loops.

    Before this existed, chargers.py and cleaning.py each listed every subtype
    manually. Same pattern, different values. DRY: one function, used in both.
    """
    return [get_stock_level(category, subtype) for subtype in subtypes]
