# Architecture Decisions

This document records the key design decisions and the reasoning behind each one.

## The Real Workflow

This system is built around how the operation actually works, not a textbook inventory model:

```
  Delivery arrives ──▶ Stock controller records it ──▶ Stock goes UP
  
  Someone needs items ──▶ Stock controller gives them out ──▶ Stock goes DOWN
                                    │
                                    ├──▶ Logs: what, how many, who received it
                                    │
                                    └──▶ If stock is now below reorder level
                                              │
                                              └──▶ Alert appears in-app
  
  End of day ──▶ Report generated: what was used, what's left
```

Items are consumables — they don't come back. There is no "return" flow. This keeps the system honest: stock only goes up (delivery) or down (given out).

## Why Transaction-Based (Not Just a Counter)

A simpler system would just store "till rolls: 50" and subtract when items go out. We don't do that because:

1. **Accountability** — Every movement records WHO gave out stock and WHO received it. If counts don't match reality, you can trace what happened.

2. **Daily reports** — To generate "used 12 till rolls today," you need individual transaction records, not just a final count.

3. **Patterns** — Over time, transaction history reveals: who uses the most stock, which days are busiest, how fast you go through chargers vs stickers. This data helps the person ordering stock plan better.

## Layered Architecture

```
  Request → Routes → Services → Storage
              │          │          │
        Validates    Enforces    Persists
        input        rules       data
```

**Routes** — Handle HTTP. Parse the request, call the right service, return the response.

**Services** — Business logic. "You can't give out more than you have." "Check if this triggers a low-stock alert." "Generate today's report." The rules of your operation live here.

**Storage** — Read and write data. Currently in-memory (Python dictionaries). Will become PostgreSQL in Phase 2. The routes and services won't change at all.

## Stock Controllers (Not a Complex Role System)

The initial design had Admin/Manager/Staff roles. That was over-engineered. The real situation:

- **2-3 stock controllers** are the only people who use the app
- They all do the same thing: give out stock and record it
- There's no need for permission levels right now

We'll add authentication in Phase 4 so each controller has their own login and transactions are tied to a name. But complex role hierarchies aren't needed.

## Alert System

Alerts are in-app only (no WhatsApp/email/SMS for now). When a stock controller logs in or records a transaction that drops stock below the reorder level, they see the alert immediately.

Each item has its own reorder threshold because usage rates differ — you might go through 50 stickers a day but only 3 till rolls. The stock controller sets these thresholds based on their experience.

## Item Categories

Seven categories, three patterns:

**Simple counters** — Till rolls, SIM cards, stickers. Just a quantity that goes up or down.

**Counters with subtypes** — Chargers (USB-C / Micro) and cleaning products (Razor / Brush / Mr Min / Label Remover). Same counter logic, but filtered by type. Each subtype has its own stock level and reorder threshold.

**Individual tracking** — Own stock devices. Tracked by serial number because each device is unique. No quantity counter — each device is a separate record.

**Status tracking** — Refurb batteries. Tracked by how many are in each stage: charging, ready, or in use. This is different from "how many do we have" — it's "where are they in the process."

## Request Lifecycle (with Middleware)

Every request passes through middleware before reaching a route handler:

```
Client Request
      │
      ▼
CORSMiddleware          ← Adds CORS headers so browsers can call the API
      │
      ▼
RequestLoggingMiddleware ← Records timestamp, method, path; attaches X-Request-ID
      │
      ▼
Route Handler           ← Does the actual work (give out stock, get dashboard, etc.)
      │
      ▼
RequestLoggingMiddleware ← Records status code and response time, writes log line
      │
      ▼
Client Response         ← Includes X-Request-ID header
```

**Request logging** — every request produces one log line:
```
2026-03-20 09:15:23 | POST   /api/till-rolls/use | 200 | 45ms | req-abc12345
```

**Request ID** — each response carries `X-Request-ID`. If a stock controller reports
an error, you can find the exact request in the logs using that ID.

**CORS** — browsers enforce same-origin policy. Without CORS headers, the future
React frontend (running on a different port) would be blocked from calling the API.
In production, `allow_origins=["*"]` should be replaced with the frontend's domain.

## Security Decisions (Still Apply)

Even with a simpler role model, these still matter:

- **UUIDs for record IDs** — Can't guess transaction IDs
- **Separate request/response models** — Server controls IDs and timestamps
- **Input validation at the boundary** — Pydantic rejects bad data immediately
- **Field length limits** — Prevents oversized payloads
- **Environment-based config** — No secrets in code