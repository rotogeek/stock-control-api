"""
memory.py - In-memory storage for stock levels and transactions
===============================================================

WHY THIS IS A SEPARATE LAYER:
Storage is its own concern. Today we use dictionaries (simple, fast, no setup).
Later (Phase 2), we'll swap this out for PostgreSQL. The service layer won't
change at all — it just calls the same storage functions and gets the same
results back, regardless of what's underneath.

This is the "repository pattern". It hides WHERE data lives from HOW it's used.
"""

import uuid
from datetime import datetime

from app.models.Inventory import (
    BatteryStatus,
    ChargerType,
    CleaningProduct,
    ItemCategory,
    MovementType,
)


# =============================================================================
# Stock Levels — current count per item
# =============================================================================
# Key: (category, subtype) — e.g. (ItemCategory.TILL_ROLL, "") or
#                                  (ItemCategory.CHARGER, ChargerType.TYPE_C)
# Value: dict with quantity and last_updated

_stock: dict[tuple, dict] = {
    (ItemCategory.TILL_ROLL, ""):                               {"quantity": 0, "last_updated": datetime.now()},
    (ItemCategory.CHARGER, ChargerType.TYPE_C):                 {"quantity": 0, "last_updated": datetime.now()},
    (ItemCategory.CHARGER, ChargerType.MICRO):                  {"quantity": 0, "last_updated": datetime.now()},
    (ItemCategory.SIM_CARD, ""):                                {"quantity": 0, "last_updated": datetime.now()},
    (ItemCategory.STICKER, ""):                                 {"quantity": 0, "last_updated": datetime.now()},
    (ItemCategory.CLEANING_PRODUCT, CleaningProduct.RAZOR):         {"quantity": 0, "last_updated": datetime.now()},
    (ItemCategory.CLEANING_PRODUCT, CleaningProduct.BRUSH):         {"quantity": 0, "last_updated": datetime.now()},
    (ItemCategory.CLEANING_PRODUCT, CleaningProduct.MR_MIN):        {"quantity": 0, "last_updated": datetime.now()},
    (ItemCategory.CLEANING_PRODUCT, CleaningProduct.LABEL_REMOVER): {"quantity": 0, "last_updated": datetime.now()},
}


# =============================================================================
# Reorder Levels — alert thresholds per item
# =============================================================================

_reorder_levels: dict[tuple, int] = {
    (ItemCategory.TILL_ROLL, ""):                               10,
    (ItemCategory.CHARGER, ChargerType.TYPE_C):                 5,
    (ItemCategory.CHARGER, ChargerType.MICRO):                  5,
    (ItemCategory.SIM_CARD, ""):                                10,
    (ItemCategory.STICKER, ""):                                 20,
    (ItemCategory.CLEANING_PRODUCT, CleaningProduct.RAZOR):         5,
    (ItemCategory.CLEANING_PRODUCT, CleaningProduct.BRUSH):         5,
    (ItemCategory.CLEANING_PRODUCT, CleaningProduct.MR_MIN):        5,
    (ItemCategory.CLEANING_PRODUCT, CleaningProduct.LABEL_REMOVER): 5,
}


# =============================================================================
# Transaction Log — every stock movement ever recorded
# =============================================================================

_transactions: list[dict] = []


# =============================================================================
# Battery Levels — how many batteries are in each charging stage
# =============================================================================
# Unlike other stock, battery "updates" are SET operations, not add/subtract.
# "10 batteries charging" replaces whatever was there before.
# We also keep a log of every update so the history is preserved.

_battery_levels: dict[str, dict] = {
    BatteryStatus.CHARGING: {"quantity": 0, "last_updated": datetime.now()},
    BatteryStatus.READY:    {"quantity": 0, "last_updated": datetime.now()},
    BatteryStatus.IN_USE:   {"quantity": 0, "last_updated": datetime.now()},
}

_battery_log: list[dict] = []


# =============================================================================
# Device Log — own-stock devices tracked by serial number
# =============================================================================
# Devices aren't counted — each one is a unique item with its own identity.
# We don't store a quantity. We store who took which serial number and when.

_device_log: list[dict] = []


# =============================================================================
# Storage Functions
# =============================================================================

def get_stock(category: str, subtype: str = "") -> int:
    """Return current quantity for an item. Returns 0 if the key is not found."""
    key = (category, subtype)
    return _stock.get(key, {}).get("quantity", 0)


def get_stock_record(category: str, subtype: str = "") -> dict:
    """Return the full stock record (quantity + last_updated)."""
    key = (category, subtype)
    return _stock.get(key, {"quantity": 0, "last_updated": datetime.now()})


def set_stock(category: str, subtype: str = "", quantity: int = 0) -> None:
    """Overwrite the stock quantity for an item and stamp the update time."""
    key = (category, subtype)
    _stock[key] = {"quantity": quantity, "last_updated": datetime.now()}


def add_stock(category: str, subtype: str = "", amount: int = 0) -> int:
    """Add to existing stock. Returns the new quantity."""
    current = get_stock(category, subtype)
    new_quantity = current + amount
    set_stock(category, subtype, new_quantity)
    return new_quantity


def subtract_stock(category: str, subtype: str = "", amount: int = 0) -> int:
    """Subtract from existing stock. Returns the new quantity."""
    current = get_stock(category, subtype)
    new_quantity = current - amount
    set_stock(category, subtype, new_quantity)
    return new_quantity


def get_reorder_level(category: str, subtype: str = "") -> int:
    """Return the reorder threshold for an item. Defaults to 0 (no alert)."""
    key = (category, subtype)
    return _reorder_levels.get(key, 0)


def set_reorder_level(category: str, subtype: str = "", level: int = 0) -> None:
    """Update the reorder threshold for an item."""
    key = (category, subtype)
    _reorder_levels[key] = level


def get_all_stock() -> list[dict]:
    """Return every stock entry as a list of flat records."""
    result = []
    for (category, subtype), record in _stock.items():
        result.append({
            "category": category,
            "subtype": subtype,
            "quantity": record["quantity"],
            "last_updated": record["last_updated"],
            "reorder_level": get_reorder_level(category, subtype),
        })
    return result


def save_transaction(
    category: str,
    subtype: str,
    movement_type: str,
    quantity: int,
    given_to: str = "",
    notes: str = "",
    recorded_by: str = "system",
) -> dict:
    """Record a stock movement and return the saved transaction."""
    transaction = {
        "id": str(uuid.uuid4()),
        "category": category,
        "subtype": subtype,
        "movement_type": movement_type,
        "quantity": quantity,
        "given_to": given_to,
        "notes": notes,
        "recorded_by": recorded_by,
        "created_at": datetime.now(),
    }
    _transactions.append(transaction)
    return transaction


def get_transactions() -> list[dict]:
    """Return a copy of all recorded transactions."""
    return list(_transactions)


# =============================================================================
# Device Storage Functions
# =============================================================================

def device_already_taken(serial_number: str) -> bool:
    """Return True if this serial number has already been logged as taken."""
    return any(d["serial_number"] == serial_number for d in _device_log)


def save_device_transaction(
    serial_number: str,
    model: str,
    given_to: str,
    notes: str = "",
    recorded_by: str = "system",
) -> dict:
    """Record a device taken from own stock and return the saved entry."""
    record = {
        "id": str(uuid.uuid4()),
        "serial_number": serial_number,
        "model": model,
        "given_to": given_to,
        "notes": notes,
        "recorded_by": recorded_by,
        "created_at": datetime.now(),
    }
    _device_log.append(record)
    return record


def get_device_log() -> list[dict]:
    """Return a copy of all device transactions."""
    return list(_device_log)


# =============================================================================
# Battery Storage Functions
# =============================================================================

def set_battery_level(status: str, quantity: int) -> None:
    """Overwrite the quantity for one battery status stage."""
    _battery_levels[status] = {"quantity": quantity, "last_updated": datetime.now()}


def get_battery_level(status: str) -> dict:
    """Return the current quantity for one battery status stage."""
    return _battery_levels.get(status, {"quantity": 0, "last_updated": datetime.now()})


def get_all_battery_levels() -> list[dict]:
    """Return current quantities for all three battery stages."""
    return [
        {"status": status, **record}
        for status, record in _battery_levels.items()
    ]


def save_battery_update(
    status: str,
    quantity: int,
    notes: str = "",
    recorded_by: str = "system",
) -> dict:
    """Record a battery status update and return the saved entry."""
    record = {
        "id": str(uuid.uuid4()),
        "status": status,
        "quantity": quantity,
        "notes": notes,
        "recorded_by": recorded_by,
        "created_at": datetime.now(),
    }
    _battery_log.append(record)
    return record
