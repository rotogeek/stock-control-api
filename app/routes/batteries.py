"""
batteries.py - Endpoints for refurb battery status tracking
============================================================

Routes in this file:
  POST /api/batteries/update  — set how many batteries are in a charging stage
  GET  /api/batteries/status  — current counts for all three stages

WHY BATTERIES ARE DIFFERENT:
Batteries cycle through stages: charging → ready → in_use.
You're not tracking "stock in" and "stock out" — you're recording WHERE
the batteries are at any point in time.

A POST to /update is a snapshot: "Right now, 10 batteries are charging,
6 are ready, 3 are in use." Each update overwrites the previous count
for that stage. The history of all updates is preserved in the log.

This is a different mental model from the other categories. The key
question is: "How many are in this state?" not "How many do I have left?"
"""

from fastapi import APIRouter

from app.models.Inventory import BatteryStatus, BatteryUpdateRequest
from app.services import stock_service

router = APIRouter(prefix="/api/batteries", tags=["Refurb Batteries"])


@router.post("/update")
def update_battery_status(request: BatteryUpdateRequest):
    """
    Record how many batteries are in a given charging stage.

    This is a SET operation — it overwrites the current count for that stage.
    Example: {"status": "charging", "quantity": 10} means 10 batteries are
    currently on charge, regardless of what was recorded before.
    """
    return stock_service.update_battery_status(
        status=request.status,
        quantity=request.quantity,
        notes=request.notes,
    )


@router.get("/status")
def get_battery_status():
    """
    Current battery counts across all three stages.

    Returns a list of three entries: charging, ready, in_use.
    Use this to see the full picture of where all batteries are right now.
    """
    return stock_service.get_battery_levels()
