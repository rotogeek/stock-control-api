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
from pydantic import BaseModel, Field, field_validator


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

class _StripStrings(BaseModel):
    """
    Mixin that strips leading/trailing whitespace from all string fields.

    Inherited by every request model so "  Thabo  " always becomes "Thabo"
    before the data reaches the service layer. Prevents name-matching bugs
    in reports (e.g. "Thabo" and " Thabo" appearing as different people).
    """
    @field_validator("*", mode="before")
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class StockUsedRequest(_StripStrings):
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


class StockReceivedRequest(_StripStrings):
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


class ChargerUsedRequest(_StripStrings):
    """Record a charger given out — includes which type."""
    charger_type: ChargerType
    quantity: int = Field(..., gt=0, le=1000)
    given_to: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(default="", max_length=500)


class ChargerReceivedRequest(_StripStrings):
    """Record chargers received from supplier."""
    charger_type: ChargerType
    quantity: int = Field(..., gt=0, le=100000)
    notes: str = Field(default="", max_length=500)


class CleaningUsedRequest(_StripStrings):
    """Record a cleaning product given out."""
    product_type: CleaningProduct
    quantity: int = Field(..., gt=0, le=1000)
    given_to: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(default="", max_length=500)


class CleaningReceivedRequest(_StripStrings):
    """Record cleaning products received from supplier."""
    product_type: CleaningProduct
    quantity: int = Field(..., gt=0, le=100000)
    notes: str = Field(default="", max_length=500)


class DeviceUsedRequest(_StripStrings):
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

    @field_validator("notes", mode="before")
    @classmethod
    def strip_notes(cls, v):
        return v.strip() if isinstance(v, str) else v


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

class BatteryStockLevel(BaseModel):
    """
    Current quantity of batteries in one charging stage, shown on the dashboard.

    Batteries aren't tracked like regular stock — there's no give-out / receive
    flow. Instead you look at the rack and record how many are in each stage.
    We surface last_updated so the controller can see when each stage was
    last counted.
    """
    status: BatteryStatus
    quantity: int
    last_updated: datetime


class DashboardResponse(BaseModel):
    """
    Full stock overview — everything the stock controller needs at a glance.

    stock_levels: all counted items (till rolls, chargers, SIM cards, etc.)
    batteries: the three charging stages with quantity and last count time.

    total_items_tracked: number of distinct stock line items being tracked.
    total_units_in_stock: sum of all quantities across every line item.
    low_stock_count: how many line items are currently below reorder level.
    last_checked: moment this snapshot was generated.
    """
    stock_levels: list[StockLevel]
    batteries: list[BatteryStockLevel]
    low_stock_alerts: list[StockLevel]  # Items currently at or below reorder level
    total_items_tracked: int            # Number of distinct line items (e.g. 9)
    total_units_in_stock: int           # Sum of all quantities (e.g. 342)
    low_stock_count: int                # How many items are currently low
    last_checked: datetime


# =============================================================================
# Configuration Model
# =============================================================================

class ReportSummary(BaseModel):
    """Top-level numbers for the daily report."""
    total_items_given_out: int
    total_items_received: int
    categories_used: int    # How many distinct item categories had activity


class ItemUsageSummary(BaseModel):
    """
    One line in the daily report — what happened to a single item type today.

    Only items with activity (given out or received) appear here.
    remaining reflects current stock, not end-of-day stock.
    """
    category: ItemCategory
    subtype: str = ""
    used_today: int
    received_today: int
    remaining: int


class PersonUsageItem(BaseModel):
    """One item line in a person's daily usage breakdown."""
    category: ItemCategory
    subtype: str = ""
    quantity: int


class PersonUsage(BaseModel):
    """All items given to one person today."""
    name: str
    items: list[PersonUsageItem]


class DailyReportResponse(BaseModel):
    """
    Full end-of-day report.

    summary: totals at a glance.
    usage_by_item: what happened to each item type today.
    usage_by_person: what each person received today.
    low_stock_alerts: items currently at or below their reorder level.
    """
    date: str
    summary: ReportSummary
    usage_by_item: list[ItemUsageSummary]
    usage_by_person: list[PersonUsage]
    low_stock_alerts: list["StockLevel"]


class TransactionResponse(BaseModel):
    """
    A single stock movement in the transaction history.

    Covers every give-out and receive across all categories, including
    device take-outs (category=own_stock_device, quantity=1).
    subtype is empty for simple items, populated for chargers and cleaning products.
    """
    id: str
    category: ItemCategory
    subtype: str = ""
    movement_type: MovementType
    quantity: int
    given_to: str = ""
    notes: str = ""
    recorded_by: str
    created_at: datetime


class TransactionListResponse(BaseModel):
    """Paginated transaction list returned by GET /api/transactions."""
    transactions: list[TransactionResponse]
    total: int        # Total matching records (before pagination)
    page: int
    per_page: int
    pages: int        # Total number of pages


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