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

from fastapi import FastAPI
from app import Config as config
from app.routes import alerts, batteries, chargers, cleaning, dashboard, devices, settings, sim_cards, stickers, till_rolls

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
    # Configuration — all under /api/settings/
    settings.router,
]

for _router in _routers:
    app.include_router(_router)


@app.get("/health")
def health_check():
    """Check if the API is running."""
    return {
        "status": "healthy",
        "service": config.APP_NAME,
        "version": "0.1.0",
        "environment": config.APP_ENV,
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