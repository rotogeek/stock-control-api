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
from app.routes import batteries, chargers, cleaning, dashboard, devices, sim_cards, stickers, till_rolls

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
# Health Check
# =============================================================================
# Every production API has this. Monitoring systems ping it to confirm
# the service is alive. If this stops responding, alerts fire.

# =============================================================================
# Register Routers
# =============================================================================
# Each router is its own file. Adding a category = one line here.

app.include_router(till_rolls.router)
app.include_router(chargers.router)
app.include_router(cleaning.router)
app.include_router(sim_cards.router)
app.include_router(stickers.router)
app.include_router(devices.router)
app.include_router(batteries.router)
app.include_router(dashboard.router)


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