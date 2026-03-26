"""
logging.py - Request logging middleware
=======================================

Runs on EVERY request, before and after the route handler.

WHY MIDDLEWARE:
You don't want to add logging to every route function — that's 20+ places
to update and easy to miss. Middleware wraps all of them automatically.
One place to add it, every request gets it.

LOG FORMAT:
    2026-03-20 09:15:23 | POST /api/till-rolls/use | 200 | 45ms
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("stock_api")
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log every incoming request with method, path, status code, and response time.

    Runs as middleware so it wraps every route automatically — no need to
    add logging to each endpoint individually.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(
            f"{timestamp} | {request.method:<6} {request.url.path} | {response.status_code} | {duration_ms}ms"
        )

        return response
