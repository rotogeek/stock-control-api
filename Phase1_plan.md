# Phase 1: Backend API — Complete Day-by-Day Plan

## What You're Building

A working API where stock controllers can:
- Record giving out items (stock goes down)
- Record deliveries arriving (stock goes up)
- See current stock levels for all 7 categories
- Get alerts when stock drops below reorder level
- Generate daily reports: what was used, by whom, what's left

## The Rules

- 5 meaningful commits per day
- Each commit is one logical piece of work
- You always have a working app — nothing half-broken gets committed
- Read the code, understand it, THEN commit it

---

## Day 1 — Project Foundation

**Goal:** Project is on GitHub. Server starts and responds.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `chore: initialize project with config and security files` | .gitignore, .env.example, LICENSE, requirements.txt | .gitignore is a security tool. Pinned versions prevent "works on my machine" bugs |
| 2 | `feat: add FastAPI application entry point and config loader` | app/\_\_init\_\_.py, app/main.py, app/config.py | How a web server starts, how env vars keep secrets out of code |
| 3 | `feat: add Pydantic models for inventory tracking` | app/models/\_\_init\_\_.py, app/models/inventory.py | Enums, validation, why request and response models are separate |
| 4 | `docs: add architecture decisions and system design` | docs/ARCHITECTURE.md | Documenting WHY matters more than documenting WHAT |
| 5 | `feat: add project README and complete package structure` | README.md, app/routes/\_\_init\_\_.py, app/services/\_\_init\_\_.py, app/storage/\_\_init\_\_.py, tests/\_\_init\_\_.py | How a professional repo looks to hiring managers |

**Test it:** Run `uvicorn app.main:app --reload`, visit `http://localhost:8000/docs`. You should see the health check endpoint.

**You have all these files already.** Follow `scripts/day1_commits.sh` to commit and push them.

---

## Day 2 — Storage Layer + First Working Endpoint

**Goal:** Give out till rolls and watch the number go down.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: add in-memory storage layer for stock levels` | app/storage/memory.py | Storage is its own layer. Data lives in dictionaries for now — we swap to PostgreSQL later without changing anything else |
| 2 | `feat: add stock service with give-out and receive logic` | app/services/stock_service.py | The service layer holds your business rules: "you can't give out more than you have" lives here |
| 3 | `feat: add till roll endpoints — use and receive` | app/routes/till_rolls.py | Connecting the layers: route calls service, service calls storage |
| 4 | `feat: register till roll routes in main application` | app/main.py (update) | FastAPI's include_router pattern — plugging routes into the app |
| 5 | `docs: add till roll API examples to README` | README.md (update) | Document what you build, when you build it |

**Concept to understand before you start:**
```
Someone sends: POST /api/till-rolls/use  {"quantity": 3, "given_to": "Thabo"}
                          ↓
Route (till_rolls.py):    Receives the request, validates the data
                          ↓
Service (stock_service.py): Checks if 3 are available. Subtracts 3. Returns result.
                          ↓
Storage (memory.py):      Updates the dictionary. Saves the transaction.
                          ↓
Response:                 {"id": "abc-123", "quantity": 3, "given_to": "Thabo", ...}
```

**Test it:** Open `/docs`, try giving out till rolls. Try giving out more than available — it should fail with a clear error.

---

## Day 3 — Chargers + Cleaning Products (Subtyped Items)

**Goal:** Handle items that have sub-categories (USB-C vs Micro, Razor vs Brush vs etc).

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: add charger endpoints with type filtering` | app/routes/chargers.py | Working with Enum subtypes — each charger type has its own stock level |
| 2 | `feat: add cleaning product endpoints` | app/routes/cleaning.py | Same pattern as chargers — recognizing reusable patterns is engineering |
| 3 | `refactor: extract shared logic into base service methods` | app/services/stock_service.py (update) | DRY principle — the give-out logic is the same for every counted item |
| 4 | `feat: register charger and cleaning routes in main app` | app/main.py (update) | Growing the app by plugging in new routers |
| 5 | `test: verify charger and cleaning endpoints via /docs` | No new files — manual testing | Test every new feature before moving on |

**Key insight:** Chargers and cleaning products follow the same pattern as till rolls, but with an extra field (charger_type or product_type). Your service layer should handle this without duplicating all the logic. If you find yourself copying and pasting, stop and refactor.

---

## Day 4 — SIM Cards, Stickers, Devices, Batteries

**Goal:** All 7 categories working. Every item type can be tracked.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: add SIM card and sticker endpoints` | app/routes/sim_cards.py, app/routes/stickers.py | These are simple counters — same as till rolls. Should be quick to add |
| 2 | `feat: add own-stock device tracking by serial number` | app/routes/devices.py, updates to service and storage | Different data pattern — individual items tracked by serial, not quantity |
| 3 | `feat: add refurb battery status tracking` | app/routes/batteries.py, updates to service and storage | Status-based tracking (charging → ready → in_use) is different from counting |
| 4 | `feat: register all remaining routes in main app` | app/main.py (update) | Your app now has all 7 categories |
| 5 | `test: end-to-end test of all 7 inventory categories` | No new files — manual testing through /docs | Testing the complete system, not just individual pieces |

**After this day:** Open `/docs` and you should see endpoints for every category. Give out items, receive deliveries, check stock levels. Everything works.

---

## Day 5 — Dashboard Endpoint + Stock Overview

**Goal:** One endpoint that shows everything — all stock levels at a glance.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: add GET /api/stock/dashboard endpoint` | app/routes/dashboard.py | Aggregating data from multiple sources into one clean response |
| 2 | `feat: add stock summary to dashboard — total items across all categories` | app/services/stock_service.py (update) | Computed fields — values calculated from other data, not stored directly |
| 3 | `feat: add last-updated timestamp to each stock level` | app/storage/memory.py (update) | Tracking metadata — when was this stock level last changed? |
| 4 | `refactor: organize all routes under /api prefix consistently` | app/main.py (update) | URL design — consistent, predictable paths are easier to use |
| 5 | `docs: add complete endpoint reference to README` | README.md (update) | Your README now documents every endpoint in the system |

**The dashboard response should look like this:**
```json
{
  "stock_levels": [
    {"category": "till_roll", "subtype": "", "current_quantity": 45, "last_updated": "..."},
    {"category": "charger", "subtype": "type_c", "current_quantity": 22, "last_updated": "..."},
    {"category": "charger", "subtype": "micro", "current_quantity": 18, "last_updated": "..."},
    {"category": "cleaning_product", "subtype": "razor", "current_quantity": 8, "last_updated": "..."}
  ],
  "total_items_tracked": 7,
  "last_checked": "2026-03-11T14:30:00"
}
```

---

## Day 6 — Low-Stock Alerts

**Goal:** The app warns stock controllers when items are running low.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: add reorder level storage with per-item thresholds` | app/storage/memory.py (update) | Configuration as data — thresholds are stored, not hardcoded |
| 2 | `feat: add PUT /api/settings/reorder-levels endpoint` | app/routes/settings.py | PUT vs POST — PUT updates existing data, POST creates new data |
| 3 | `feat: add alert checking after every stock give-out` | app/services/stock_service.py (update) | Trigger logic — something happens automatically BECAUSE of a state change |
| 4 | `feat: add GET /api/alerts endpoint returning items below threshold` | app/routes/alerts.py | Filtering — return only items where current_quantity <= reorder_level |
| 5 | `feat: include is_low flag in dashboard stock levels` | app/routes/dashboard.py (update), app/models/inventory.py (if needed) | Enriching existing data — add useful info without breaking existing consumers |

**Test it:**
1. Set till roll reorder level to 10: `PUT /api/settings/reorder-levels/till_roll` with `{"reorder_level": 10}`
2. Check stock: till rolls at 45. No alert.
3. Give out 40 till rolls. Stock now at 5.
4. Check `GET /api/alerts` — till rolls should appear.
5. Check dashboard — till rolls should show `"is_low": true`.

---

## Day 7 — Transaction History

**Goal:** Every stock movement is recorded and queryable. This is the foundation for daily reports.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: store complete transaction history for all movements` | app/storage/memory.py (update) | Transaction log — every change is an event stored permanently, not just a counter update |
| 2 | `feat: add GET /api/transactions endpoint with date filtering` | app/routes/transactions.py | Query parameters — ?date=2026-03-11 filters results, datetime handling in Python |
| 3 | `feat: add filtering by category and person` | app/routes/transactions.py (update) | Multiple filters — ?category=charger&given_to=Thabo |
| 4 | `feat: add pagination to transaction list` | app/routes/transactions.py (update) | Pagination — never return unlimited data, use ?page=1&per_page=20 |
| 5 | `feat: register transaction routes and update docs` | app/main.py (update), README.md (update) | Growing the app methodically |

**Why transactions matter:**
Without a transaction log, you only know "till rolls: 45." With a log, you know:
- Thabo received 3 till rolls at 9:15am
- Sipho received 2 till rolls at 10:30am
- A delivery of 50 arrived at 2:00pm

This history is what makes daily reports possible (Day 8) and what makes your system trustworthy. In fintech, this pattern is called an "event log" or "ledger" — same principle that powers bank account statements.

---

## Day 8 — Daily Reports

**Goal:** Generate "end of day" report: what was used, who received what, what's left.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: add daily report generation in service layer` | app/services/report_service.py | New service — separating report logic from stock logic |
| 2 | `feat: add GET /api/reports/daily endpoint` | app/routes/reports.py | Returns today's report by default, accepts ?date= for historical reports |
| 3 | `feat: add per-person breakdown to daily report` | app/services/report_service.py (update) | Grouping — "Thabo: 3 chargers, 1 till roll. Sipho: 2 SIM cards" |
| 4 | `feat: add low-stock warnings section to daily report` | app/services/report_service.py (update) | Combining alerts + report — one view of everything important |
| 5 | `docs: add sample daily report output to README` | README.md (update) | Showing exactly what the system produces |

**The daily report should look like this:**
```json
{
  "date": "2026-03-11",
  "summary": {
    "total_items_given_out": 23,
    "total_items_received": 100,
    "categories_used": 5
  },
  "usage_by_item": [
    {"category": "till_roll", "used_today": 8, "received_today": 0, "remaining": 37},
    {"category": "charger", "subtype": "type_c", "used_today": 5, "received_today": 50, "remaining": 67}
  ],
  "usage_by_person": [
    {"name": "Thabo", "items": [{"category": "charger", "subtype": "type_c", "quantity": 3}]},
    {"name": "Sipho", "items": [{"category": "till_roll", "quantity": 5}]}
  ],
  "low_stock_alerts": [
    {"category": "sticker", "current_quantity": 4, "reorder_level": 20}
  ]
}
```

---

## Day 9 — Error Handling + Edge Cases

**Goal:** The API handles every bad input gracefully with clear, consistent errors.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `fix: return clear error when giving out more than available stock` | app/services/stock_service.py (update) | Custom error messages: "Cannot give out 50 till rolls. Only 12 in stock." |
| 2 | `feat: add consistent error response format` | app/models/errors.py | All errors return same shape: {"error": "insufficient_stock", "detail": "...", "status_code": 400} |
| 3 | `fix: handle edge cases — zero stock, empty category, missing reorder level` | app/services/stock_service.py (update) | Boundary bugs — most bugs live at 0, at empty, at the edge |
| 4 | `feat: add input sanitization — strip whitespace from names` | app/services/stock_service.py (update) | "  Thabo  " should become "Thabo". Whitespace causes matching bugs in reports |
| 5 | `test: document all error scenarios and expected responses` | docs/ERROR_HANDLING.md | Error documentation — what can go wrong and what the API returns |

**Error response format (use this everywhere):**
```json
{
  "error": "insufficient_stock",
  "detail": "Cannot give out 50 till rolls. Only 12 currently in stock.",
  "status_code": 400
}
```

---

## Day 10 — Request Logging + Middleware

**Goal:** Every API request is logged. You can see who did what and when.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: add request logging middleware` | app/middleware/logging.py | Middleware runs on EVERY request. Logs: timestamp, method, path, status code |
| 2 | `feat: add request ID to every response header` | app/middleware/logging.py (update) | Request tracing — when something goes wrong, you can find the exact request |
| 3 | `feat: register middleware in main application` | app/main.py (update) | How middleware plugs into FastAPI |
| 4 | `feat: add CORS middleware for frontend preparation` | app/main.py (update) | CORS — browsers block cross-origin requests by default. This allows your future React app to talk to the API |
| 5 | `docs: add middleware documentation to ARCHITECTURE.md` | docs/ARCHITECTURE.md (update) | Documenting the request lifecycle |

**What the logs look like:**
```
2026-03-20 09:15:23 | POST /api/till-rolls/use | 200 | 45ms | req-abc123
2026-03-20 09:15:30 | POST /api/chargers/use | 400 | 12ms | req-def456
2026-03-20 09:16:01 | GET  /api/stock/dashboard | 200 | 23ms | req-ghi789
```

---

## Day 11 — Polish + Cleanup

**Goal:** Clean, consistent, professional codebase. No rough edges.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `refactor: ensure all endpoints follow consistent naming convention` | Multiple route files | API design consistency — /api/category/action everywhere |
| 2 | `refactor: remove any duplicated logic across services` | app/services/ | Final DRY pass — if logic appears twice, extract it |
| 3 | `feat: add GET /api/health/detailed for system status` | app/main.py (update) | Returns: uptime, total transactions recorded, number of active alerts |
| 4 | `style: clean up comments, remove TODOs, fix formatting` | Multiple files | Code hygiene — production code has no "TODO: fix this later" |
| 5 | `docs: update all documentation to reflect final Phase 1 state` | README.md, ARCHITECTURE.md | Docs match reality. Nothing outdated. |

---

## Day 12 — Review + Phase 1 Wrap

**Goal:** You can explain every line of code. Everything works. Everything is documented.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `test: add complete endpoint test checklist` | docs/TESTING.md | A checklist of every endpoint and its expected behavior |
| 2 | `test: verify all 7 categories end-to-end through /docs` | No new files — testing | Systematic testing — go through the checklist |
| 3 | `fix: any bugs found during final testing` | Various | Every project has bugs found in final testing |
| 4 | `docs: add Phase 1 retrospective to ARCHITECTURE.md` | docs/ARCHITECTURE.md (update) | What went well, what was hard, what you'd do differently |
| 5 | `chore: tag Phase 1 release — v0.1.0` | No files — git tag | Git tags mark milestones: `git tag -a v0.1.0 -m "Phase 1: Backend API complete"` |

**After Day 12:** Run `git log --oneline` and you should see 60 clean commits telling the story of a professional backend API being built step by step.

---

## Phase 1 Endpoint Summary

When Phase 1 is complete, your API has these endpoints:

| Method | Endpoint | What It Does |
|---|---|---|
| GET | /health | Health check |
| GET | /api/stock/dashboard | All stock levels at a glance |
| GET | /api/alerts | Items below reorder level |
| GET | /api/transactions | Full history with filtering |
| GET | /api/reports/daily | Daily usage report |
| POST | /api/till-rolls/use | Record till rolls given out |
| POST | /api/till-rolls/receive | Record till roll delivery |
| POST | /api/chargers/use | Record chargers given out |
| POST | /api/chargers/receive | Record charger delivery |
| POST | /api/cleaning/use | Record cleaning products given out |
| POST | /api/cleaning/receive | Record cleaning product delivery |
| POST | /api/sim-cards/use | Record SIM cards given out |
| POST | /api/sim-cards/receive | Record SIM card delivery |
| POST | /api/stickers/use | Record stickers given out |
| POST | /api/stickers/receive | Record sticker delivery |
| POST | /api/devices/take | Record device taken from own stock |
| POST | /api/batteries/update | Update battery charging status |
| PUT | /api/settings/reorder-levels/{category} | Set reorder threshold |
| GET | /api/settings/reorder-levels | View all thresholds |

---

## Commit Message Quick Reference

```
feat:     New feature              feat: add charger endpoints with type filtering
fix:      Bug fix                  fix: return error when stock is insufficient
refactor: Restructure code         refactor: extract shared route logic into helpers
docs:     Documentation            docs: add daily report examples to README
test:     Testing                  test: verify all endpoints via /docs
chore:    Config/maintenance       chore: tag Phase 1 release v0.1.0
style:    Formatting only          style: fix indentation in stock service
```

---

## Daily Routine

```
1. Read today's plan in this document
2. git pull (if working from multiple machines)
3. Build commit 1 → test it → git add → git commit
4. Build commit 2 → test it → git add → git commit
5. Build commit 3 → test it → git add → git commit
6. Build commit 4 → test it → git add → git commit
7. Build commit 5 → test it → git add → git commit
8. git push
9. Check GitHub — verify commits look clean
10. Read tomorrow's plan
```