# Error Handling

Every error from this API returns the same JSON shape:

```json
{
  "error": "insufficient_stock",
  "detail": "Cannot give out 5 type_c charger(s). Only 2 currently in stock.",
  "status_code": 400
}
```

| Field        | Description                                      |
|---|---|
| `error`      | Machine-readable code — use this in switch statements |
| `detail`     | Human-readable message — suitable for logs and UI display |
| `status_code`| Mirrors the HTTP status code |

---

## Error Codes

### `insufficient_stock` — 400

Raised when a give-out quantity exceeds what's currently in stock.

```
POST /api/till-rolls/use  {"quantity": 50, "given_to": "Thabo"}
→ 400 {"error": "insufficient_stock", "detail": "Cannot give out 50 till roll(s). Only 12 currently in stock.", "status_code": 400}
```

**Fix:** Check `GET /api/<category>/stock` first, or reduce the quantity.

---

### `duplicate_serial` — 400

Raised when a device serial number has already been logged as taken.

```
POST /api/devices/take  {"serial_number": "SN123456", ...}
→ 400 {"error": "duplicate_serial", "detail": "Device SN123456 has already been logged as taken.", "status_code": 400}
```

**Fix:** Check `GET /api/devices/log` to confirm whether the device was already recorded.

---

### `invalid_date` — 400

Raised when a `?date=` parameter is not a valid YYYY-MM-DD string.

```
GET /api/transactions?date=25-03-2026
→ 400 {"error": "invalid_date", "detail": "Invalid date format: '25-03-2026'. Use YYYY-MM-DD (e.g. 2026-03-25).", "status_code": 400}
```

**Fix:** Use ISO 8601 format: `2026-03-25`.

---

### `invalid_category` — 400

Raised when an unknown category string is passed to `?category=` or to the settings endpoint.

```
GET /api/transactions?category=cables
→ 400 {"error": "invalid_category", "detail": "Unknown category: 'cables'. Valid values: ['charger', 'cleaning_product', ...].", "status_code": 400}

PUT /api/settings/reorder-levels/cables
→ 400 {"error": "invalid_category", "detail": "Unknown category: 'cables'. Valid values: [...].", "status_code": 400}
```

**Valid category values:**
- `till_roll`
- `charger`
- `sim_card`
- `own_stock_device`
- `refurb_battery`
- `cleaning_product`
- `sticker`

---

## Validation Errors — 422

FastAPI validates request bodies automatically using Pydantic. If a required field is missing or a value is out of range, you get a 422 before the request reaches business logic.

```
POST /api/till-rolls/use  {"quantity": -1, "given_to": "Thabo"}
→ 422 {"detail": [{"type": "greater_than", "loc": ["body", "quantity"], ...}]}
```

Common causes:
- `quantity` ≤ 0 (must be at least 1)
- `given_to` is empty or missing
- `charger_type` / `product_type` / `status` is not one of the valid enum values
- `reorder_level` is negative

---

## Edge Cases

| Scenario | Behaviour |
|---|---|
| Give out exactly the last unit in stock | Succeeds. Stock goes to 0. If `reorder_level > 0`, an alert fires. |
| Give out 0 quantity | Rejected with 422 — Pydantic `gt=0` constraint. |
| Receive stock when at 0 | Succeeds — no minimum stock check on deliveries. |
| Set reorder level to 0 | Disables alerting for that item (`0` means "no threshold"). |
| Name with surrounding whitespace (`"  Thabo  "`) | Stripped to `"Thabo"` at the model layer before saving. |
| Duplicate serial number for devices | Rejected with 400 `duplicate_serial`. |
| `?date=` with past date (no transactions) | Returns empty list / empty report — not an error. |
