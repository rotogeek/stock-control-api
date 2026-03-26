# Phase 1 — Endpoint Test Checklist

Manual testing guide for every endpoint. Run through this before any release.
All testing is done via the interactive docs at `http://localhost:8000/docs`.

---

## Setup

1. Start the server: `uvicorn app.Main:app --reload`
2. Open `http://localhost:8000/docs`
3. Work through each section in order — stock must exist before you can give it out

---

## Health & System

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 1 | `GET /health` | Hit the endpoint | `{"status": "healthy", ...}` |
| 2 | `GET /api/health/detailed` | Hit the endpoint | Shows uptime_seconds, total_transactions_recorded, active_low_stock_alerts |
| 3 | `GET /` | Hit the root URL | Returns links to /docs and /health |

---

## Till Rolls

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 4 | `POST /api/till-rolls/receive` | `{"quantity": 50, "notes": ""}` | 200, returns transaction record |
| 5 | `GET /api/till-rolls/stock` | — | `current_quantity: 50` |
| 6 | `POST /api/till-rolls/use` | `{"quantity": 3, "given_to": "Thabo"}` | 200, returns transaction record |
| 7 | `GET /api/till-rolls/stock` | — | `current_quantity: 47` |
| 8 | `POST /api/till-rolls/use` | `{"quantity": 999}` | 400, `insufficient_stock` error |
| 9 | `POST /api/till-rolls/use` | `{"quantity": 0, "given_to": "Thabo"}` | 422, Pydantic validation error |

---

## Chargers

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 10 | `POST /api/chargers/receive` | `{"charger_type": "type_c", "quantity": 20}` | 200 |
| 11 | `POST /api/chargers/receive` | `{"charger_type": "micro", "quantity": 15}` | 200 |
| 12 | `GET /api/chargers/stock` | — | Both type_c (20) and micro (15) shown |
| 13 | `GET /api/chargers/stock/type_c` | — | type_c stock only |
| 14 | `POST /api/chargers/use` | `{"charger_type": "type_c", "quantity": 2, "given_to": "Sipho"}` | 200 |
| 15 | `POST /api/chargers/use` | `{"charger_type": "type_c", "quantity": 999}` | 400, insufficient_stock |

---

## Cleaning Products

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 16 | `POST /api/cleaning/receive` | `{"product_type": "razor", "quantity": 10}` | 200 |
| 17 | `POST /api/cleaning/receive` | `{"product_type": "brush", "quantity": 8}` | 200 |
| 18 | `GET /api/cleaning/stock` | — | All 4 product types shown |
| 19 | `GET /api/cleaning/stock/razor` | — | Razor stock only |
| 20 | `POST /api/cleaning/use` | `{"product_type": "razor", "quantity": 3, "given_to": "Thabo"}` | 200 |

---

## SIM Cards

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 21 | `POST /api/sim-cards/receive` | `{"quantity": 100}` | 200 |
| 22 | `GET /api/sim-cards/stock` | — | `current_quantity: 100` |
| 23 | `POST /api/sim-cards/use` | `{"quantity": 5, "given_to": "Sipho"}` | 200 |
| 24 | `GET /api/sim-cards/stock` | — | `current_quantity: 95` |

---

## Stickers

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 25 | `POST /api/stickers/receive` | `{"quantity": 200}` | 200 |
| 26 | `POST /api/stickers/use` | `{"quantity": 10, "given_to": "Thabo"}` | 200 |
| 27 | `GET /api/stickers/stock` | — | `current_quantity: 190` |

---

## Own-Stock Devices

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 28 | `POST /api/devices/take` | `{"serial_number": "SN001", "model": "Samsung A15", "given_to": "Thabo"}` | 200 |
| 29 | `POST /api/devices/take` | Same serial number again | 400, `duplicate_serial` error |
| 30 | `POST /api/devices/take` | `{"serial_number": "SN002", "model": "iPhone 11", "given_to": "Sipho"}` | 200 |
| 31 | `GET /api/devices/log` | — | Both devices shown |

---

## Refurb Batteries

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 32 | `POST /api/batteries/update` | `{"status": "charging", "quantity": 20}` | 200 |
| 33 | `POST /api/batteries/update` | `{"status": "ready", "quantity": 15}` | 200 |
| 34 | `POST /api/batteries/update` | `{"status": "in_use", "quantity": 8}` | 200 |
| 35 | `GET /api/batteries/status` | — | All three stages shown with correct quantities |
| 36 | `POST /api/batteries/update` | `{"status": "charging", "quantity": 18}` | 200 — SET overwrites, doesn't add |

---

## Dashboard

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 37 | `GET /api/stock/dashboard` | After all above | All categories shown, batteries shown, totals correct |
| 38 | Check `low_stock_count` | — | Reflects items below their reorder threshold |
| 39 | Check `is_low` flags | — | Items at/below reorder_level have `is_low: true` |

---

## Low-Stock Alerts

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 40 | `PUT /api/settings/reorder-levels/till_roll` | `{"reorder_level": 50}` | 200 — till rolls now at 47, which is below 50 |
| 41 | `GET /api/alerts` | — | Till rolls appear as low-stock |
| 42 | `PUT /api/settings/reorder-levels/charger?subtype=type_c` | `{"reorder_level": 5}` | 200 |
| 43 | `GET /api/settings/reorder-levels` | — | All thresholds shown including new ones |
| 44 | `PUT /api/settings/reorder-levels/till_roll` | `{"reorder_level": 0}` | 200 — alerting disabled |
| 45 | `GET /api/alerts` | — | Till rolls no longer appear |

---

## Transaction History

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 46 | `GET /api/transactions` | — | All movements so far, paginated |
| 47 | `GET /api/transactions?given_to=thabo` | — | Only Thabo's transactions |
| 48 | `GET /api/transactions?category=charger` | — | Only charger movements |
| 49 | `GET /api/transactions?date=2026-03-26` | Today's date | Today's transactions only |
| 50 | `GET /api/transactions?date=2099-01-01` | Future date | Empty list (not an error) |
| 51 | `GET /api/transactions?date=not-a-date` | — | 400, `invalid_date` error |
| 52 | `GET /api/transactions?page=1&per_page=5` | — | Max 5 results, `pages` reflects total |

---

## Daily Report

| # | Endpoint | Test | Expected |
|---|---|---|---|
| 53 | `GET /api/reports/daily` | — | Today's activity grouped by item and person |
| 54 | Check `usage_by_person` | — | Thabo and Sipho shown with their items |
| 55 | Check `usage_by_item` | — | Only items with activity appear |
| 56 | `GET /api/reports/daily?date=2099-01-01` | Future date | Empty report (no transactions) |
| 57 | `GET /api/reports/daily?date=bad-date` | — | 400, `invalid_date` error |
| 58 | `GET /api/reports/daily/low-stock` | — | Items currently at or below reorder level |

---

## Input Validation

| # | Test | Expected |
|---|---|---|
| 59 | `given_to: "  Thabo  "` (with spaces) | Stored as `"Thabo"` — whitespace stripped |
| 60 | `given_to: ""` (empty) | 422 validation error |
| 61 | `quantity: -1` | 422 validation error |
| 62 | `quantity: 0` | 422 validation error |
| 63 | `category: "invalid_thing"` in transactions filter | 400, `invalid_category` error |

---

## Request Tracing

| # | Test | Expected |
|---|---|---|
| 64 | Any request | Response includes `X-Request-ID` header |
| 65 | Any request | Server console shows log line with timestamp, method, path, status, duration, request ID |
