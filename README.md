# Stock Control API

A FastAPI backend for tracking inventory in a device refurbishment operation.
Stock controllers record items given out and deliveries received across 7 categories.

---

## Running the API

```bash
uvicorn app.Main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

---

## Endpoint Reference

### Dashboard

#### All stock levels at a glance
```
GET /api/stock/dashboard
```

**Response (200):**
```json
{
  "stock_levels": [
    {
      "category": "till_roll",
      "subtype": "",
      "current_quantity": 45,
      "reorder_level": 10,
      "is_low": false,
      "last_updated": "2026-03-24T09:00:00"
    },
    {
      "category": "charger",
      "subtype": "type_c",
      "current_quantity": 22,
      "reorder_level": 5,
      "is_low": false,
      "last_updated": "2026-03-24T09:00:00"
    }
  ],
  "batteries": [
    {"status": "charging", "quantity": 10, "last_updated": "2026-03-24T08:30:00"},
    {"status": "ready",    "quantity": 25, "last_updated": "2026-03-24T08:30:00"},
    {"status": "in_use",   "quantity": 8,  "last_updated": "2026-03-24T08:30:00"}
  ],
  "total_items_tracked": 9,
  "total_units_in_stock": 342,
  "low_stock_count": 1,
  "last_checked": "2026-03-24T09:15:00"
}
```

---

### Till Rolls

#### Give out till rolls
```
POST /api/till-rolls/use
```
```json
{"quantity": 3, "given_to": "Thabo", "notes": "For till 4"}
```

#### Record a delivery
```
POST /api/till-rolls/receive
```
```json
{"quantity": 100, "notes": "Supplier: Office Depot, invoice #4421"}
```

#### Check current stock level
```
GET /api/till-rolls/stock
```

---

### Chargers

#### Give out chargers
```
POST /api/chargers/use
```
```json
{"charger_type": "type_c", "quantity": 2, "given_to": "Sipho", "notes": ""}
```
`charger_type`: `type_c` or `micro`

#### Record a delivery
```
POST /api/chargers/receive
```
```json
{"charger_type": "micro", "quantity": 50, "notes": ""}
```

#### Check stock — all types
```
GET /api/chargers/stock
```

#### Check stock — one type
```
GET /api/chargers/stock/{charger_type}
```

---

### Cleaning Products

#### Give out cleaning products
```
POST /api/cleaning/use
```
```json
{"product_type": "razor", "quantity": 5, "given_to": "Thabo", "notes": ""}
```
`product_type`: `razor`, `brush`, `mr_min`, or `label_remover`

#### Record a delivery
```
POST /api/cleaning/receive
```
```json
{"product_type": "mr_min", "quantity": 20, "notes": ""}
```

#### Check stock — all products
```
GET /api/cleaning/stock
```

#### Check stock — one product
```
GET /api/cleaning/stock/{product_type}
```

---

### SIM Cards

#### Give out SIM cards
```
POST /api/sim-cards/use
```
```json
{"quantity": 2, "given_to": "Thabo", "notes": ""}
```

#### Record a delivery
```
POST /api/sim-cards/receive
```
```json
{"quantity": 200, "notes": ""}
```

#### Check current stock level
```
GET /api/sim-cards/stock
```

---

### Stickers

#### Give out stickers
```
POST /api/stickers/use
```
```json
{"quantity": 10, "given_to": "Sipho", "notes": ""}
```

#### Record a delivery
```
POST /api/stickers/receive
```
```json
{"quantity": 500, "notes": ""}
```

#### Check current stock level
```
GET /api/stickers/stock
```

---

### Own-Stock Devices

#### Record a device taken from stock
```
POST /api/devices/take
```
```json
{
  "serial_number": "SN123456",
  "model": "Samsung A15",
  "given_to": "Thabo",
  "notes": ""
}
```
Each serial number can only be logged once. Returns 400 if already taken.

#### View device log
```
GET /api/devices/log
```

---

### Refurb Batteries

#### Update battery count for a stage
```
POST /api/batteries/update
```
```json
{"status": "charging", "quantity": 12, "notes": ""}
```
`status`: `charging`, `ready`, or `in_use`

This is a **SET** operation — "12 batteries charging" means the count IS 12, not that 12 more were added.

#### Check current battery status
```
GET /api/batteries/status
```

---

### Daily Reports

#### Full daily report
```
GET /api/reports/daily
GET /api/reports/daily?date=2026-03-25
```

Defaults to today. Pass `?date=` for historical reports.

**Response (200):**
```json
{
  "date": "2026-03-25",
  "summary": {
    "total_items_given_out": 23,
    "total_items_received": 100,
    "categories_used": 5
  },
  "usage_by_item": [
    {
      "category": "till_roll",
      "subtype": "",
      "used_today": 8,
      "received_today": 0,
      "remaining": 37
    },
    {
      "category": "charger",
      "subtype": "type_c",
      "used_today": 5,
      "received_today": 50,
      "remaining": 67
    }
  ],
  "usage_by_person": [
    {
      "name": "Sipho",
      "items": [{"category": "till_roll", "subtype": "", "quantity": 5}]
    },
    {
      "name": "Thabo",
      "items": [{"category": "charger", "subtype": "type_c", "quantity": 3}]
    }
  ],
  "low_stock_alerts": [
    {
      "category": "sticker",
      "subtype": "",
      "current_quantity": 4,
      "reorder_level": 20,
      "is_low": true,
      "last_updated": "2026-03-25T14:00:00"
    }
  ]
}
```

Only items with activity (given out or received) appear in `usage_by_item`.
Only recipients with give-outs appear in `usage_by_person`.

#### Low-stock warnings only
```
GET /api/reports/daily/low-stock
```

Returns just the low-stock alerts — items currently at or below their reorder level.
Shortcut for quick checks without loading the full report.

---

### Transaction History

#### List all stock movements
```
GET /api/transactions
```

Returns every give-out and delivery across all categories, paginated.

**Query parameters (all optional):**

| Parameter | Type | Description |
|---|---|---|
| `date` | `YYYY-MM-DD` | Only movements on that day |
| `category` | string | e.g. `charger`, `till_roll`, `sim_card` |
| `given_to` | string | Case-insensitive name search |
| `page` | int | Page number (default: 1) |
| `per_page` | int | Results per page (default: 20, max: 100) |

**Examples:**
```
GET /api/transactions
GET /api/transactions?date=2026-03-25
GET /api/transactions?category=charger&given_to=thabo
GET /api/transactions?date=2026-03-25&page=2&per_page=10
```

**Response (200):**
```json
{
  "transactions": [
    {
      "id": "abc-123",
      "category": "charger",
      "subtype": "type_c",
      "movement_type": "used",
      "quantity": 2,
      "given_to": "Thabo",
      "notes": "",
      "recorded_by": "stock_controller",
      "created_at": "2026-03-25T09:15:00"
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

The `X-Total-Count` response header also contains the total number of matching records.

---

### System

#### Health check
```
GET /health
```
```json
{"status": "healthy", "service": "stock-control-api", "version": "0.1.0", "environment": "development"}
```

---

## Error Responses

**Not enough stock (400):**
```json
{"detail": "Cannot give out 50 till roll(s). Only 12 currently in stock."}
```

**Device already logged (400):**
```json
{"detail": "Device SN123456 has already been logged as taken."}
```
