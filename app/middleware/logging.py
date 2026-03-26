"""
logging.py - Request logging middleware
=======================================

Runs on EVERY request, before and after the route handler.

WHY MIDDLEWARE:
You don't want to add logging to every route function — that's 20+ places
to update and easy to miss. Middleware wraps all of them automatically.
One place to add it, every request gets it.

LOG FORMAT:
    2026-03-20 09:15:23 | POST   /api/till-rolls/use | 200 | 45ms | req-abc12345

REQUEST ID:
Each request gets a unique X-Request-ID header in the response.
When something goes wrong, you can match the log line to the exact request.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("stock_api")
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log every incoming request and attach a unique request ID to the response.

    Log line includes: timestamp, HTTP method, path, status code, duration, request ID.
    Response header X-Request-ID lets clients trace a specific request in the logs.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = f"req-{str(uuid.uuid4())[:8]}"
        start = time.time()

        response = await call_next(request)

        duration_ms = round((time.time() - start) * 1000)
        response.headers["X-Request-ID"] = request_id

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(
            f"{timestamp} | {request.method:<6} {request.url.path} | {response.status_code} | {duration_ms}ms | {request_id}"
        )

        return response
