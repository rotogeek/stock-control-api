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

## Till Roll Endpoints

### Give out till rolls

```
POST /api/till-rolls/use
```

```json
{
  "quantity": 3,
  "given_to": "Thabo",
  "notes": "For till 4"
}
```

**Success response (200):**
```json
{
  "id": "a1b2c3d4-...",
  "category": "till_roll",
  "subtype": "",
  "movement_type": "used",
  "quantity": 3,
  "given_to": "Thabo",
  "notes": "For till 4",
  "recorded_by": "stock_controller",
  "created_at": "2026-03-12T09:15:00"
}
```

**Error — not enough stock (400):**
```json
{
  "detail": "Cannot give out 50 till roll(s). Only 12 currently in stock."
}
```

---

### Record a delivery

```
POST /api/till-rolls/receive
```

```json
{
  "quantity": 100,
  "notes": "Supplier: Office Depot, invoice #4421"
}
```

**Success response (200):**
```json
{
  "id": "e5f6g7h8-...",
  "category": "till_roll",
  "subtype": "",
  "movement_type": "received",
  "quantity": 100,
  "given_to": "",
  "notes": "Supplier: Office Depot, invoice #4421",
  "recorded_by": "stock_controller",
  "created_at": "2026-03-12T14:00:00"
}
```

---

### Check current stock level

```
GET /api/till-rolls/stock
```

**Response (200):**
```json
{
  "category": "till_roll",
  "subtype": "",
  "current_quantity": 97,
  "reorder_level": 10,
  "is_low": false,
  "last_updated": "2026-03-12T14:00:00"
}
```

---

## Health Check

```
GET /health
```

```json
{
  "status": "healthy",
  "service": "stock-control-api",
  "version": "0.1.0",
  "environment": "development"
}
```
