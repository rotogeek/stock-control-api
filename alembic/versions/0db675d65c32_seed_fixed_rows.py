"""seed fixed rows

Revision ID: 0db675d65c32
Revises: 7a0bcd581af5
Create Date: 2026-04-19 15:45:07.363291

WHY THIS MIGRATION EXISTS:
Two tables have a fixed, pre-defined set of rows that must exist for the
application to work — they are never inserted or deleted during normal use,
only updated in-place.

  stock_levels   — 9 rows, one per item line the stock controller manages.
                   quantity starts at 0; the controller will set real numbers
                   via the API on first use.

  battery_levels — 3 rows, one per charging stage (charging / ready / in_use).
                   quantity starts at 0 for the same reason.

If these rows don't exist, every API read would return 404 or crash.
"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0db675d65c32'
down_revision: Union[str, None] = '7a0bcd581af5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    now = datetime.now()

    # -------------------------------------------------------------------------
    # stock_levels — 9 fixed rows
    # -------------------------------------------------------------------------
    # Simple counters (no subtype — subtype stored as empty string)
    #   till_roll, sim_card, sticker
    # Subtypes
    #   charger:           type_c, micro
    #   cleaning_product:  razor, brush, mr_min, label_remover
    # -------------------------------------------------------------------------
    op.bulk_insert(
        sa.table(
            "stock_levels",
            sa.column("category", sa.String),
            sa.column("subtype", sa.String),
            sa.column("quantity", sa.Integer),
            sa.column("reorder_level", sa.Integer),
            sa.column("last_updated", sa.DateTime),
        ),
        [
            # Simple counters
            {"category": "TILL_ROLL",         "subtype": "",               "quantity": 0, "reorder_level": 0, "last_updated": now},
            {"category": "SIM_CARD",          "subtype": "",               "quantity": 0, "reorder_level": 0, "last_updated": now},
            {"category": "STICKER",           "subtype": "",               "quantity": 0, "reorder_level": 0, "last_updated": now},
            # Charger subtypes
            {"category": "CHARGER",           "subtype": "type_c",         "quantity": 0, "reorder_level": 0, "last_updated": now},
            {"category": "CHARGER",           "subtype": "micro",          "quantity": 0, "reorder_level": 0, "last_updated": now},
            # Cleaning product subtypes
            {"category": "CLEANING_PRODUCT",  "subtype": "razor",          "quantity": 0, "reorder_level": 0, "last_updated": now},
            {"category": "CLEANING_PRODUCT",  "subtype": "brush",          "quantity": 0, "reorder_level": 0, "last_updated": now},
            {"category": "CLEANING_PRODUCT",  "subtype": "mr_min",         "quantity": 0, "reorder_level": 0, "last_updated": now},
            {"category": "CLEANING_PRODUCT",  "subtype": "label_remover",  "quantity": 0, "reorder_level": 0, "last_updated": now},
        ],
    )

    # -------------------------------------------------------------------------
    # battery_levels — 3 fixed rows (one per charging stage)
    # -------------------------------------------------------------------------
    op.bulk_insert(
        sa.table(
            "battery_levels",
            sa.column("status", sa.String),
            sa.column("quantity", sa.Integer),
            sa.column("last_updated", sa.DateTime),
        ),
        [
            {"status": "CHARGING", "quantity": 0, "last_updated": now},
            {"status": "READY",    "quantity": 0, "last_updated": now},
            {"status": "IN_USE",   "quantity": 0, "last_updated": now},
        ],
    )


def downgrade() -> None:
    # Remove seed data in reverse table order.
    op.execute("DELETE FROM battery_levels")
    op.execute("DELETE FROM stock_levels")
