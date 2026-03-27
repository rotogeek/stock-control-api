"""
orm.py - SQLAlchemy ORM table definitions
==========================================

WHY A SEPARATE FILE:
Pydantic models (Inventory.py) describe what the API sends and receives.
ORM models (this file) describe what lives in the database. They are different
concerns. Pydantic validates HTTP data; SQLAlchemy maps Python objects to rows.

TABLE OVERVIEW:

  stock_levels       — 9 fixed rows. Current quantity + reorder threshold
                       per item. Composite PK: (category, subtype).
                       e.g. ("charger", "type_c") or ("till_roll", "")

  transactions       — Unbounded log. Every give-out and receive across
                       all simple/subtype categories. One row per event.

  device_transactions — Devices taken from own stock, by serial number.
                       One row per device handed out.

  battery_levels     — 3 fixed rows (charging / ready / in_use).
                       Records the current count for each stage.

  battery_updates    — Unbounded log. Every time a battery count is
                       updated, a row is appended here.

  alerts             — Unbounded log. A row is written whenever a
                       give-out causes stock to hit/cross reorder level.

WHY NO SURROGATE KEY ON stock_levels / battery_levels:
These tables have a small, fixed number of rows that are looked up by their
natural key (category+subtype, or status). A surrogate UUID would add noise
with no benefit.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.Inventory import BatteryStatus, ItemCategory, MovementType


# =============================================================================
# stock_levels — current quantity and reorder threshold per item line
# =============================================================================

class StockLevel(Base):
    """
    One row per item line.

    There are exactly 9 rows (pre-seeded by Alembic, Day 3):
        till_roll / ""
        charger   / type_c
        charger   / micro
        sim_card  / ""
        sticker   / ""
        cleaning_product / razor
        cleaning_product / brush
        cleaning_product / mr_min
        cleaning_product / label_remover

    quantity and reorder_level are updated in-place — these rows are never
    deleted or inserted during normal operation.
    """
    __tablename__ = "stock_levels"

    category = Column(
        Enum(ItemCategory, name="item_category", create_type=False),
        primary_key=True,
        nullable=False,
    )
    subtype = Column(
        String(50),
        primary_key=True,
        nullable=False,
        default="",
    )
    quantity = Column(
        Integer,
        nullable=False,
        default=0,
    )
    reorder_level = Column(
        Integer,
        nullable=False,
        default=0,
    )
    last_updated = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_stock_quantity_non_negative"),
        CheckConstraint("reorder_level >= 0", name="ck_stock_reorder_non_negative"),
    )

    def __repr__(self):
        return f"<StockLevel {self.category}/{self.subtype} qty={self.quantity}>"


# =============================================================================
# transactions — every give-out and receive across simple/subtype categories
# =============================================================================

class Transaction(Base):
    """
    One row per stock movement (give-out or receive).

    subtype is empty string for simple items (till_roll, sim_card, sticker).
    given_to is empty string for received deliveries (no person, just supplier).
    recorded_by is "stock_controller" until Phase 4 introduces real auth.
    """
    __tablename__ = "transactions"

    id = Column(
        String(36),    # UUID stored as string — consistent with memory.py
        primary_key=True,
        nullable=False,
    )
    category = Column(
        Enum(ItemCategory, name="item_category", create_type=False),
        nullable=False,
    )
    subtype = Column(
        String(50),
        nullable=False,
        default="",
    )
    movement_type = Column(
        Enum(MovementType, name="movement_type", create_type=False),
        nullable=False,
    )
    quantity = Column(
        Integer,
        nullable=False,
    )
    given_to = Column(
        String(200),
        nullable=False,
        default="",
    )
    notes = Column(
        String(500),
        nullable=False,
        default="",
    )
    recorded_by = Column(
        String(200),
        nullable=False,
        default="stock_controller",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_transaction_quantity_positive"),
    )

    def __repr__(self):
        return (
            f"<Transaction {self.id[:8]} "
            f"{self.movement_type}/{self.category} qty={self.quantity}>"
        )


# =============================================================================
# device_transactions — own-stock devices taken out by serial number
# =============================================================================

class DeviceTransaction(Base):
    """
    One row per device handed out.

    Devices are tracked individually — each has a unique serial number.
    There is no "receive" event for devices (they arrive as own-stock,
    not via the normal give-out/receive flow).

    serial_number is not unique at the table level because the same device
    could theoretically be re-issued after being returned (future Phase).
    For now, the service layer enforces no-duplicate in a single pass.
    """
    __tablename__ = "device_transactions"

    id = Column(String(36), primary_key=True, nullable=False)
    serial_number = Column(String(100), nullable=False)
    model = Column(String(200), nullable=False)
    given_to = Column(String(200), nullable=False)
    notes = Column(String(500), nullable=False, default="")
    recorded_by = Column(String(200), nullable=False, default="stock_controller")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<DeviceTransaction {self.serial_number} → {self.given_to}>"


# =============================================================================
# battery_levels — current quantity for each charging stage
# =============================================================================

class BatteryLevel(Base):
    """
    Exactly 3 rows: charging / ready / in_use.

    Unlike normal stock, batteries are SET (not incremented/decremented).
    The stock controller looks at the rack and says "10 are charging" —
    that number replaces whatever was there before.

    quantity is updated in-place. Each update also appends a BatteryUpdate row.
    """
    __tablename__ = "battery_levels"

    status = Column(
        Enum(BatteryStatus, name="battery_status", create_type=False),
        primary_key=True,
        nullable=False,
    )
    quantity = Column(Integer, nullable=False, default=0)
    last_updated = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_battery_quantity_non_negative"),
    )

    def __repr__(self):
        return f"<BatteryLevel {self.status} qty={self.quantity}>"


# =============================================================================
# battery_updates — log of every battery count update
# =============================================================================

class BatteryUpdate(Base):
    """
    Append-only log. One row written every time a battery stage is counted.

    This preserves history — you can see that on Monday 10 were charging,
    by Wednesday 7 were charging. battery_levels only shows the current count.
    """
    __tablename__ = "battery_updates"

    id = Column(String(36), primary_key=True, nullable=False)
    status = Column(
        Enum(BatteryStatus, name="battery_status", create_type=False),
        nullable=False,
    )
    quantity = Column(Integer, nullable=False)
    notes = Column(String(500), nullable=False, default="")
    recorded_by = Column(String(200), nullable=False, default="stock_controller")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_battery_update_quantity_non_negative"),
    )

    def __repr__(self):
        return f"<BatteryUpdate {self.status} qty={self.quantity}>"


# =============================================================================
# alerts — log of every low-stock alert fired
# =============================================================================

class Alert(Base):
    """
    Append-only log. A row is written whenever a give-out causes stock to
    reach or drop below the reorder level for that item.

    This is a historical log — it records WHEN alerts fired, not just whether
    an item is currently low. To see what is currently low, query stock_levels
    where quantity <= reorder_level.
    """
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, nullable=False)
    category = Column(
        Enum(ItemCategory, name="item_category", create_type=False),
        nullable=False,
    )
    subtype = Column(String(50), nullable=False, default="")
    current_quantity = Column(Integer, nullable=False)
    reorder_level = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<Alert {self.category}/{self.subtype} qty={self.current_quantity}>"
