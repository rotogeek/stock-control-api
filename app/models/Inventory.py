"""
inventory.py - Data models for the stock control system
=========================================================

THE REAL WORKFLOW (this is what actually happens on the floor):

  1. Stock controller logs in
  2. Someone comes and asks for items (charger, till roll, etc.)
  3. Stock controller hands it out and records: what, how many, who got it
  4. Stock level goes DOWN
  5. If stock drops below the reorder level → alert appears in the app
  6. When a new delivery arrives → stock controller records it, stock goes UP
  7. End of day → report shows what was used and what's left

That's it. No returns. No adjustments. Stock goes out or comes in.
"""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


# =============================================================================
# Enums — The fixed categories in your operation
# =============================================================================

class ChargerType(str, Enum):
    """The two charger connector types you stock."""
    TYPE_C = "type_c"
    MICRO = "micro"


class CleaningProduct(str, Enum):
    """Cleaning products used in refurbishment."""
    RAZOR = "razor"
    BRUSH = "brush"
    MR_MIN = "mr_min"
    LABEL_REMOVER = "label_remover"


class MovementType(str, Enum):
    """
    Only two things happen to stock:
      - USED: given out to someone (stock goes DOWN)
      - RECEIVED: new delivery arrived (stock goes UP)
    
    That's it. No "adjust", no "return". Keep it real.
    """
    USED = "used"
    RECEIVED = "received"


class BatteryStatus(str, Enum):
    """Where a refurb battery is in the charging cycle."""
    CHARGING = "charging"
    READY = "ready"
    IN_USE = "in_use"


class ItemCategory(str, Enum):
    """
    All seven inventory categories in your operation.
    Used for alerts, reports, and the dashboard.
    """
    TILL_ROLL = "till_roll"
    CHARGER = "charger"
    SIM_CARD = "sim_card"
    OWN_STOCK_DEVICE = "own_stock_device"
    REFURB_BATTERY = "refurb_battery"
    CLEANING_PRODUCT = "cleaning_product"
    STICKER = "sticker"


# =============================================================================
# Request Models — What stock controllers send to the API
# =============================================================================

class StockUsedRequest(BaseModel):
    """
    Record that stock was given out to someone.
    
    This is the most common action. A stock controller hands items out
    and logs: what they gave, how many, and who received it.
    
    Example: "Gave 2 type-c chargers to Thabo"
    """
    quantity: int = Field(
        ...,
        gt=0,
        le=1000,
        description="How many items were given out"
    )
    given_to: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the person who received the items"
    )
    notes: str = Field(
        default="",
        max_length=500,
        description="Optional note (e.g. reason, job reference)"
    )


class StockReceivedRequest(BaseModel):
    """
    Record that new stock arrived (delivery from supplier).
    
    Example: "Received 100 stickers from supplier"
    """
    quantity: int = Field(
        ...,
        gt=0,
        le=100000,
        description="How many items arrived"
    )
    notes: str = Field(
        default="",
        max_length=500,
        description="Optional note (e.g. supplier name, invoice number)"
    )


class ChargerUsedRequest(BaseModel):
    """Record a charger given out — includes which type."""
    charger_type: ChargerType
    quantity: int = Field(..., gt=0, le=1000)
    given_to: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(default="", max_length=500)


class ChargerReceivedRequest(BaseModel):
    """Record chargers received from supplier."""
    charger_type: ChargerType
    quantity: int = Field(..., gt=0, le=100000)
    notes: str = Field(default="", max_length=500)


class CleaningUsedRequest(BaseModel):
    """Record a cleaning product given out."""
    product_type: CleaningProduct
    quantity: int = Field(..., gt=0, le=1000)
    given_to: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(default="", max_length=500)


class CleaningReceivedRequest(BaseModel):
    """Record cleaning products received from supplier."""
    product_type: CleaningProduct
    quantity: int = Field(..., gt=0, le=100000)
    notes: str = Field(default="", max_length=500)


class DeviceUsedRequest(BaseModel):
    """
    Record a device taken from own stock.
    
    Devices are tracked individually by serial number because
    each one is unique — unlike chargers where you just count them.
    """
    serial_number: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=200)
    given_to: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(default="", max_length=500)


class BatteryUpdateRequest(BaseModel):
    """
    Update how many batteries are in each charging stage.
    
    Unlike other items, batteries cycle through statuses:
    charging → ready → in_use. You're tracking WHERE they are
    in the process, not just a count.
    """
    status: BatteryStatus
    quantity: int = Field(..., gt=0, le=1000)
    notes: str = Field(default="", max_length=500)


# =============================================================================
# Response Models — What the API sends back
# =============================================================================

class StockMovementResponse(BaseModel):
    """Response after recording any stock movement."""
    id: str
    category: ItemCategory
    movement_type: MovementType
    quantity: int
    given_to: str = ""
    notes: str = ""
    recorded_by: str          # Which stock controller logged this
    created_at: datetime


class DeviceMovementResponse(BaseModel):
    """Response after recording a device taken from own stock."""
    id: str
    serial_number: str
    model: str
    given_to: str
    notes: str
    recorded_by: str
    created_at: datetime


class BatteryStatusResponse(BaseModel):
    """Response after updating battery status."""
    id: str
    status: BatteryStatus
    quantity: int
    notes: str
    recorded_by: str
    created_at: datetime


# =============================================================================
# Dashboard & Reporting Models
# =============================================================================

class StockLevel(BaseModel):
    """
    Current stock level for one item on the dashboard.
    
    This is what the stock controller sees when they log in:
    the item, how many are left, and whether it needs reordering.
    """
    category: ItemCategory
    subtype: str = ""          # e.g. "type_c" for chargers, "razor" for cleaning
    current_quantity: int
    reorder_level: int         # Alert threshold — set per item
    is_low: bool               # True when current_quantity <= reorder_level
    last_updated: datetime


class DailyUsageSummary(BaseModel):
    """
    One line in the end-of-day report.
    
    Example: "Till Rolls — Used today: 12 — Remaining: 38"
    """
    category: ItemCategory
    subtype: str = ""
    used_today: int
    received_today: int
    remaining: int


class DailyReport(BaseModel):
    """
    The full end-of-day report sent to the stock controller.
    
    Shows everything that happened today and current stock levels.
    """
    date: str                                # "2026-03-10"
    items: list[DailyUsageSummary]           # One entry per item type
    total_items_given_out: int               # Grand total across all categories
    low_stock_alerts: list[StockLevel]       # Items below reorder level


class AlertNotification(BaseModel):
    """
    In-app alert when stock drops below reorder level.
    
    This appears in the app when the stock controller is logged in.
    """
    category: ItemCategory
    subtype: str = ""
    current_quantity: int
    reorder_level: int
    message: str               # e.g. "Till Rolls are low! 3 remaining (reorder at 10)"
    created_at: datetime


# =============================================================================
# Dashboard Model
# =============================================================================

class DashboardResponse(BaseModel):
    """
    Full stock overview — everything the stock controller needs at a glance.

    stock_levels covers all counted items (till rolls, chargers, SIM cards, etc.)
    Each entry shows quantity, reorder threshold, and whether it is low.

    total_items_tracked is the number of distinct stock line items.
    last_checked is the moment this snapshot was generated.
    """
    stock_levels: list[StockLevel]
    total_items_tracked: int
    last_checked: datetime


# =============================================================================
# Configuration Model
# =============================================================================

class ReorderLevelUpdate(BaseModel):
    """
    Set the reorder threshold for an item.
    
    When stock drops to or below this number, an alert fires.
    Each item can have a different threshold because you use
    stickers faster than you use label remover.
    """
    reorder_level: int = Field(
        ...,
        ge=0,        # ge = greater than or equal. 0 means "no alert"
        le=10000,
        description="Alert when stock drops to this number or below"
    )