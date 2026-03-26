"""
main.py - The entry point of your Stock Control API
=====================================================

This file creates the FastAPI application and registers all routes.
Think of it as the front door — it directs requests to the right place
but doesn't contain the actual logic.

HOW TO RUN:
    uvicorn app.main:app --reload

    - app.main   → look in app/ folder, find main.py
    - :app       → use the variable called 'app'
    - --reload   → restart when files change (development only)

Once running, visit http://localhost:8000/docs for interactive API docs.
"""

from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app import Config as config
from app.middleware.logging import RequestLoggingMiddleware
from app.models.errors import StockAPIError
from app.routes import alerts, batteries, chargers, cleaning, dashboard, devices, reports, settings, sim_cards, stickers, till_rolls, transactions
from app.storage import memory as storage

_start_time = datetime.now()

# =============================================================================
# Create the Application
# =============================================================================
# These parameters become the API documentation header.
# Visit /docs after starting the server to see them rendered.

app = FastAPI(
    title="Stock Control API",
    description="Inventory management for device refurbishment operations",
    version="0.1.0",
)


# =============================================================================
# Register Routers
# =============================================================================
# Every route in this API lives under /api/... — consistent prefix throughout.
# To add a new category: create app/routes/your_category.py with an APIRouter
# using prefix="/api/your-category", then add it to this list. One line.

_routers = [
    # Stock categories — all under /api/<category-name>/
    till_rolls.router,
    chargers.router,
    cleaning.router,
    sim_cards.router,
    stickers.router,
    devices.router,
    batteries.router,
    # Aggregation & reporting — all under /api/stock/
    dashboard.router,
    # Alerts — /api/alerts
    alerts.router,
    # Transaction history — /api/transactions
    transactions.router,
    # Reports — /api/reports/
    reports.router,
    # Configuration — all under /api/settings/
    settings.router,
]

for _router in _routers:
    app.include_router(_router)


# =============================================================================
# Middleware
# =============================================================================
# Middleware wraps every request — runs before the route handler and after.
# Order matters: middleware added last runs outermost (first on the way in).

app.add_middleware(RequestLoggingMiddleware)

# CORS — browsers block cross-origin requests by default. Without this,
# a React frontend running on localhost:3000 cannot call this API on :8000.
# In production, replace "*" with the exact frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Error Handlers
# =============================================================================
# Every StockAPIError raised anywhere in the app is caught here and returned
# in the consistent format: {"error": "...", "detail": "...", "status_code": ...}

@app.exception_handler(StockAPIError)
async def stock_error_handler(request: Request, exc: StockAPIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error,
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.get("/health")
def health_check():
    """Check if the API is running."""
    return {
        "status": "healthy",
        "service": config.APP_NAME,
        "version": "0.1.0",
        "environment": config.APP_ENV,
    }


@app.get("/api/health/detailed")
def health_detailed():
    """
    Detailed system status — uptime, transaction count, and active alert count.

    Use this to get a quick picture of system activity without loading the
    full dashboard. Useful for monitoring and ops checks.
    """
    uptime = datetime.now() - _start_time
    total_transactions = len(storage.get_transactions())
    active_alerts = len([
        item for item in storage.get_all_stock()
        if item["reorder_level"] > 0 and item["quantity"] <= item["reorder_level"]
    ])

    return {
        "status": "healthy",
        "version": "0.1.0",
        "uptime_seconds": int(uptime.total_seconds()),
        "total_transactions_recorded": total_transactions,
        "active_low_stock_alerts": active_alerts,
        "started_at": _start_time.isoformat(),
    }


# =============================================================================
# Root
# =============================================================================
# Friendly response at the base URL. Better than a 404 error.

@app.get("/")
def root():
    """Base URL — points to documentation."""
    return {
        "message": "Stock Control API",
        "docs": "/docs",
        "health": "/health",
    }