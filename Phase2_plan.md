# Phase 2: PostgreSQL Database — Complete Day-by-Day Plan

## What You're Building

Replace the in-memory Python dictionaries with a real PostgreSQL database.
When the server restarts, all stock levels, transactions, and alerts survive.

The API stays identical — same endpoints, same responses. Only the storage
layer changes. This is the whole point of building it as a separate layer in Phase 1.

## What's New vs Phase 1

- **PostgreSQL** — relational database running as a system service
- **SQLAlchemy** — Python library for talking to the database in Python, not raw SQL
- **Alembic** — tool for managing database schema changes (adding/changing tables)
- **Sessions** — each API request opens a DB connection, uses it, closes it cleanly

## The Rules (same as Phase 1)

- 5 meaningful commits per day
- Each commit is one logical piece of work
- You always have a working app — nothing half-broken gets committed
- Read the code, understand it, THEN commit it

---

## Day 1 — Install PostgreSQL + Verify Connection

**Goal:** PostgreSQL is installed, running, and the API can connect to it.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `chore: install PostgreSQL and add DB dependencies to requirements` | Requirement.txt | psycopg2-binary is the driver — SQLAlchemy speaks Python, psycopg2 speaks PostgreSQL |
| 2 | `chore: create stockcontrol database and user` | No files — terminal commands | PostgreSQL security model: each app gets its own user with only the permissions it needs |
| 3 | `feat: add database connection module with SQLAlchemy engine` | app/database.py | Engine = connection factory. Session = one conversation with the database |
| 4 | `feat: update DATABASE_URL config and .env.example` | app/Config.py (update), .env.example (update) | Connection strings: `postgresql://user:password@host:port/dbname` |
| 5 | `feat: add database connection check to /api/health/detailed` | app/Main.py (update) | The health endpoint now tells you if the DB is reachable, not just if the server is up |

**Terminal commands for this day:**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start it
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create your database and user
sudo -u postgres psql
```
Inside psql:
```sql
CREATE USER stockcontrol WITH PASSWORD 'stockcontrol123';
CREATE DATABASE stockcontroldb OWNER stockcontrol;
\q
```

**.env file to create:**
```
DATABASE_URL=postgresql://stockcontrol:stockcontrol123@localhost:5432/stockcontroldb
```

**New packages to add to Requirement.txt:**
```
SQLAlchemy==2.0.36
psycopg2-binary==2.9.10
alembic==1.14.0
```

**Test it:** Run the server, hit `GET /api/health/detailed` — it should show `"database": "connected"`.

---

## Day 2 — Schema Design + SQLAlchemy Models

**Goal:** Every table is defined as a Python class. You understand the schema before writing a single migration.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: add StockLevel database model` | app/models/database.py | SQLAlchemy ORM: a Python class maps to a database table, a class instance maps to a row |
| 2 | `feat: add Transaction database model` | app/models/database.py (update) | Columns, types, defaults — INTEGER, VARCHAR, TIMESTAMP, UUID |
| 3 | `feat: add ReorderLevel and Alert database models` | app/models/database.py (update) | Primary keys, nullable fields, why every table needs a clear identifier |
| 4 | `feat: add BatteryLevel and DeviceLog database models` | app/models/database.py (update) | UNIQUE constraint on serial_number — the database enforces uniqueness, not just your code |
| 5 | `docs: add database schema diagram to ARCHITECTURE.md` | docs/ARCHITECTURE.md (update) | Documenting the schema helps you spot problems before writing code |

**The schema (what you're building):**

```
stock_levels          transactions              reorder_levels
─────────────         ───────────────────       ──────────────
category (PK)         id UUID (PK)              category (PK)
subtype  (PK)         category                  subtype  (PK)
quantity              subtype                   reorder_level
last_updated          movement_type
                      quantity
battery_levels        given_to                  alerts
──────────────        notes                     ───────────────
status   (PK)         recorded_by               id UUID (PK)
quantity              created_at                category
last_updated                                    subtype
                      device_log                current_quantity
                      ──────────────────        reorder_level
                      id UUID (PK)              message
                      serial_number (UNIQUE)    created_at
                      model
                      given_to
                      notes
                      recorded_by
                      created_at
```

**Key decisions documented here:**
- `stock_levels` uses a composite primary key `(category, subtype)` — same structure as the in-memory dict key
- `transactions.id` is a UUID, not an auto-increment integer — UUIDs don't reveal how many records exist
- `device_log.serial_number` has a UNIQUE constraint — the database enforces this, not just your code

---

## Day 3 — Alembic Migrations

**Goal:** Alembic is configured. Running `alembic upgrade head` creates all tables in PostgreSQL.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `chore: initialise Alembic migrations` | alembic.ini, alembic/, alembic/env.py | Migration tool setup — Alembic tracks which migrations have run so it never runs one twice |
| 2 | `feat: write initial migration — create all Phase 2 tables` | alembic/versions/001_create_tables.py | `op.create_table()` — this is the SQL CREATE TABLE, written in Python |
| 3 | `feat: add downgrade path to initial migration` | alembic/versions/001_create_tables.py (update) | `upgrade()` creates tables, `downgrade()` drops them — always write both so you can roll back |
| 4 | `chore: run migration and verify tables exist in PostgreSQL` | No files — terminal command | `alembic upgrade head` applies the migration. `\dt` in psql shows the tables |
| 5 | `docs: add migration workflow to ARCHITECTURE.md` | docs/ARCHITECTURE.md (update) | How to add a new column in the future: write a migration, run it, done |

**Commands for this day:**
```bash
# Initialise Alembic
alembic init alembic

# Create the first migration (you write this manually)
# Then apply it
alembic upgrade head

# Verify in psql
sudo -u postgres psql -d stockcontroldb
\dt        # show all tables
\d transactions    # show columns of the transactions table
```

**Test it:** All 6 tables exist in PostgreSQL.

---

## Day 4 — Rewrite Stock Levels Storage

**Goal:** `get_stock`, `set_stock`, `add_stock`, `subtract_stock` all read/write PostgreSQL. The service layer is unchanged.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: add database session dependency for FastAPI routes` | app/database.py (update) | FastAPI's `Depends()` — inject a DB session into any route that needs one |
| 2 | `feat: rewrite get_stock and get_stock_record to query PostgreSQL` | app/storage/memory.py → app/storage/db.py | `session.query(StockLevel).filter_by(...)` replaces `_stock.get(key)` |
| 3 | `feat: rewrite set_stock, add_stock, subtract_stock to use PostgreSQL` | app/storage/db.py (update) | `session.merge()` — INSERT if the row doesn't exist, UPDATE if it does (upsert) |
| 4 | `feat: rewrite get_all_stock to query all stock_levels rows` | app/storage/db.py (update) | `session.query(StockLevel).all()` returns every row as a list of objects |
| 5 | `test: verify stock levels survive server restart` | No files — manual test | Give out stock → restart the server → check the level is still correct. This only works with a real database |

**Key concept:**
```python
# BEFORE (memory.py):
def get_stock(category, subtype=""):
    return _stock.get((category, subtype), {}).get("quantity", 0)

# AFTER (db.py):
def get_stock(session, category, subtype=""):
    row = session.query(StockLevel).filter_by(category=category, subtype=subtype).first()
    return row.quantity if row else 0
```

The function signature gains a `session` parameter. That's the only change the service layer sees.

---

## Day 5 — Rewrite Transaction Log Storage

**Goal:** Every give-out and delivery is saved to the `transactions` table. `GET /api/transactions` queries PostgreSQL.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: rewrite save_transaction to insert into PostgreSQL` | app/storage/db.py (update) | `session.add(Transaction(...))` + `session.commit()` — write a row, confirm it's saved |
| 2 | `feat: rewrite get_transactions with PostgreSQL filtering` | app/storage/db.py (update) | `.filter()` chains — date filter, category filter, given_to ILIKE search |
| 3 | `feat: add ILIKE for case-insensitive name search in PostgreSQL` | app/storage/db.py (update) | `ILIKE '%thabo%'` in PostgreSQL is the database-native way to do case-insensitive substring matching |
| 4 | `feat: move pagination to the database query` | app/storage/db.py (update) | `.offset().limit()` — the database paginates, not Python. More efficient on large datasets |
| 5 | `test: verify transactions persist and filters work correctly` | No files — manual test | Record transactions, restart server, query with filters — data should survive and filters should match |

**Key concept — moving filtering to the DB:**
```python
# BEFORE (memory.py) — filters in Python after loading everything:
transactions = _transactions  # load all into memory
transactions = [t for t in transactions if ...]  # filter in Python

# AFTER (db.py) — filters in the SQL query:
query = session.query(Transaction)
if given_to:
    query = query.filter(Transaction.given_to.ilike(f"%{given_to}%"))
total = query.count()
rows = query.offset(offset).limit(per_page).all()
```

The database does the work. Python doesn't load 10,000 records to return 20.

---

## Day 6 — Reorder Levels + Alerts

**Goal:** Reorder thresholds and alert history are stored in PostgreSQL.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: rewrite reorder level storage to use PostgreSQL` | app/storage/db.py (update) | `get_reorder_level`, `set_reorder_level`, `get_all_reorder_levels` — same interface, DB backend |
| 2 | `feat: seed default reorder levels on first run` | app/database.py (update) | App startup logic — if the reorder_levels table is empty, insert the defaults |
| 3 | `feat: rewrite save_alert and get_alert_log to use PostgreSQL` | app/storage/db.py (update) | Append-only log — alerts are never updated, only inserted |
| 4 | `feat: verify low-stock alert flow end-to-end with PostgreSQL` | No files — manual test | Give out stock → alert saved to DB → restart → alert still there |
| 5 | `docs: document seeding strategy in ARCHITECTURE.md` | docs/ARCHITECTURE.md (update) | Why seeding matters: without defaults, every item starts with reorder_level=0 (no alerts ever fire) |

---

## Day 7 — Device Log + Battery Levels

**Goal:** Devices and batteries read/write PostgreSQL. Duplicate serial check uses a DB UNIQUE constraint.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: rewrite device storage to use PostgreSQL` | app/storage/db.py (update) | `device_already_taken` queries the DB instead of scanning a list |
| 2 | `feat: use database UNIQUE constraint for serial number enforcement` | app/storage/db.py (update) | The DB enforces uniqueness — if your code has a bug, the database still catches duplicate serials |
| 3 | `feat: rewrite battery level storage to use PostgreSQL` | app/storage/db.py (update) | `session.merge()` for battery upsert — same pattern as stock levels |
| 4 | `feat: rewrite battery update log to use PostgreSQL` | app/storage/db.py (update) | Battery history is now queryable: every stage update is a permanent record |
| 5 | `test: verify device and battery data persist across restarts` | No files — manual test | Log a device, restart, check the device_log — serial should still be there and duplicate should still be rejected |

---

## Day 8 — Wire Routes to the Database

**Goal:** All routes pass a DB session to the storage layer. The in-memory module is removed.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `refactor: update till roll and charger routes to inject DB session` | app/routes/till_rolls.py, chargers.py | FastAPI `Depends(get_db)` — the framework creates and closes sessions automatically |
| 2 | `refactor: update cleaning, sim card, and sticker routes` | app/routes/cleaning.py, sim_cards.py, stickers.py | Same pattern applied to remaining simple-counter routes |
| 3 | `refactor: update device, battery, and dashboard routes` | app/routes/devices.py, batteries.py, dashboard.py | Every route that touches storage needs a session |
| 4 | `refactor: update alerts, transactions, reports, and settings routes` | app/routes/alerts.py, transactions.py, reports.py, settings.py | Report service reads from DB; alert service queries live stock |
| 5 | `chore: remove in-memory storage module` | app/storage/memory.py (delete) | The old module is gone. If anything still imports it, you'll know immediately |

---

## Day 9 — Database Error Handling

**Goal:** DB failures return clean errors. Transactions roll back on failure. The app doesn't crash.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: add database error handler to main application` | app/Main.py (update), app/models/errors.py (update) | `SQLAlchemyError` — catch DB errors the same way you catch `StockAPIError` |
| 2 | `feat: wrap all write operations in try/except with rollback` | app/storage/db.py (update) | If saving a transaction fails halfway, rollback undoes the partial write. The data stays consistent |
| 3 | `feat: add connection failure detection to health endpoint` | app/Main.py (update) | If the database is down, the health endpoint says so clearly instead of returning a confusing 500 |
| 4 | `fix: handle IntegrityError on duplicate serial number` | app/storage/db.py (update) | The DB raises `IntegrityError` on UNIQUE violations — catch it and return your clean `duplicate_serial` error |
| 5 | `docs: update ERROR_HANDLING.md with database error scenarios` | docs/ERROR_HANDLING.md (update) | What happens when the DB is down? When a constraint is violated? Document it |

---

## Day 10 — Connection Pooling + Environment Config

**Goal:** The app manages DB connections efficiently. Config is clean and production-ready.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `feat: configure SQLAlchemy connection pool` | app/database.py (update) | Pool size, max overflow, timeout — a pool reuses connections instead of opening a new one per request |
| 2 | `feat: add DATABASE_URL validation on startup` | app/database.py (update) | Fail fast — if DATABASE_URL is missing or wrong, crash at startup with a clear message, not on the first request |
| 3 | `feat: add .env.example with all required variables` | .env.example (update) | Document every variable a new developer needs to set |
| 4 | `refactor: move all DB config constants to Config.py` | app/Config.py (update) | Pool size, timeout, echo mode — not hardcoded in database.py, read from environment |
| 5 | `docs: add production deployment notes to README` | README.md (update) | What to set differently in production: DEBUG=false, a real DATABASE_URL, a real SECRET_KEY |

---

## Day 11 — Polish + Full Test Run

**Goal:** Clean code, complete test coverage, no rough edges.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `refactor: ensure session lifecycle is consistent across all routes` | app/routes/ (review) | Sessions must always close — using `Depends(get_db)` with a generator ensures this even if an error occurs |
| 2 | `refactor: remove any remaining references to in-memory storage` | Multiple files | `grep -r "memory" app/` — any hit is a bug |
| 3 | `test: run full endpoint test checklist against PostgreSQL backend` | docs/TESTING.md (update) | Every check in TESTING.md, now backed by a real database |
| 4 | `style: clean up database module comments and formatting` | app/database.py, app/storage/db.py | Code that future you can read without notes |
| 5 | `docs: update ARCHITECTURE.md to reflect Phase 2 storage layer` | docs/ARCHITECTURE.md (update) | The storage diagram now shows PostgreSQL, not Python dicts |

---

## Day 12 — Review + Phase 2 Wrap

**Goal:** You can explain every SQL query. Data persists. Everything is documented.

| # | Commit | Files | What You Learn |
|---|---|---|---|
| 1 | `test: verify all data persists correctly across server restarts` | No files — testing | The ultimate test of Phase 2: restart the server 3 times and check nothing is lost |
| 2 | `test: verify concurrent requests don't corrupt stock levels` | No files — testing | Open two browser tabs, give out stock from both simultaneously, count should be correct |
| 3 | `fix: any bugs found during final testing` | Various | Every project has bugs found in final testing |
| 4 | `docs: add Phase 2 retrospective to ARCHITECTURE.md` | docs/ARCHITECTURE.md (update) | What SQLAlchemy abstracts, what it exposes, what you'd do differently |
| 5 | `chore: tag Phase 2 release — v0.2.0` | No files — git tag | `git tag -a v0.2.0 -m "Phase 2: PostgreSQL database"` |

---

## Phase 2 File Changes Summary

| File | Action |
|---|---|
| `app/database.py` | **New** — engine, session factory, `get_db` dependency |
| `app/models/database.py` | **New** — SQLAlchemy ORM models (table definitions) |
| `app/storage/db.py` | **New** — all storage functions, DB-backed |
| `app/storage/memory.py` | **Deleted** — replaced entirely |
| `alembic/` | **New** — migration directory |
| `alembic.ini` | **New** — Alembic config |
| `Requirement.txt` | **Updated** — add SQLAlchemy, psycopg2-binary, alembic |
| `app/Config.py` | **Updated** — DB pool config vars |
| `.env.example` | **Updated** — DATABASE_URL documented |
| `app/Main.py` | **Updated** — DB error handler, startup check |
| `app/routes/*.py` | **Updated** — all routes inject `session` via `Depends(get_db)` |
| `docs/ARCHITECTURE.md` | **Updated** — schema diagram, Phase 2 retrospective |
| `docs/TESTING.md` | **Updated** — re-verified against PostgreSQL |

---

## The Key Concept of Phase 2

```
Phase 1 storage layer:         Phase 2 storage layer:
─────────────────────          ─────────────────────
Routes                         Routes
  │                              │
Services                       Services
  │                              │
memory.py                      db.py
  │                              │
Python dicts (lost              PostgreSQL
on restart)                    (persists forever)
```

Routes and services don't change. Only what's behind the storage interface changes.
This is why the layered architecture mattered in Phase 1 — it makes Phase 2 possible
without touching 80% of the codebase.

---

## Commit Message Quick Reference

```
feat:     New feature
fix:      Bug fix
refactor: Restructure code
docs:     Documentation
test:     Testing
chore:    Config/maintenance
style:    Formatting only
```
