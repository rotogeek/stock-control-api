"""
devices.py - Endpoints for own-stock device tracking
=====================================================

Routes in this file:
  POST /api/devices/take  — record a device taken from own stock
  GET  /api/devices/log   — view all devices that have been taken

WHY THIS IS DIFFERENT FROM OTHER CATEGORIES:
Every other category tracks a count: "47 type-C chargers left."
Devices are tracked individually: "iPhone 12, serial XYZ123, given to Thabo."

There is no quantity — a device is either in stock or it's been taken.
There is no receive endpoint — own-stock devices come from the refurb
process, not a supplier delivery. They enter the system a different way.

The serial number is the identity. Taking the same serial number twice is
blocked — that would mean logging a phantom device.
"""

from fastapi import APIRouter

from app.models.Inventory import DeviceUsedRequest
from app.services import stock_service

router = APIRouter(prefix="/api/devices", tags=["Own-Stock Devices"])


@router.post("/take")
def take_device(request: DeviceUsedRequest):
    """
    Record a device taken from own stock.

    Requires serial_number and model — both are recorded permanently.
    Returns 400 if that serial number has already been logged as taken.
    """
    return stock_service.take_device(
        serial_number=request.serial_number,
        model=request.model,
        given_to=request.given_to,
        notes=request.notes,
    )


@router.get("/log")
def get_device_log():
    """
    View all devices that have been taken from own stock.

    Useful for auditing: who took which device, and when.
    """
    return stock_service.get_device_log()
