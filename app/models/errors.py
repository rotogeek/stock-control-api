"""
errors.py - Custom exception and error response model
=======================================================

WHY A CONSISTENT ERROR FORMAT:
Without this, errors come back in different shapes depending on what
went wrong. FastAPI validation errors look different from business rule
errors, which look different from not-found errors. That makes it hard
for API consumers to handle errors reliably.

Every error from this API returns the same shape:
  {
    "error": "insufficient_stock",     ← machine-readable code
    "detail": "Cannot give out...",    ← human-readable message
    "status_code": 400                 ← mirrors the HTTP status
  }

The error code lets consumers write switch statements.
The detail message is for logging and displaying to users.

USAGE:
  raise StockAPIError(
      error="insufficient_stock",
      detail="Cannot give out 5 type_c charger(s). Only 2 in stock.",
  )

  raise StockAPIError(
      error="not_found",
      detail="No stock record found for category: invalid_type",
      status_code=404,
  )
"""

from pydantic import BaseModel


class StockAPIError(Exception):
    """
    Raised when a business rule is violated or a resource is not found.

    error:       Machine-readable error code (e.g. "insufficient_stock")
    detail:      Human-readable explanation shown to API consumers
    status_code: HTTP status code — 400 for bad requests, 404 for not found
    """
    def __init__(self, error: str, detail: str, status_code: int = 400):
        self.error = error
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class ErrorResponse(BaseModel):
    """
    The shape every error from this API returns.

    Registered as the response_model for error cases in route docstrings
    so it appears correctly in /docs.
    """
    error: str
    detail: str
    status_code: int
