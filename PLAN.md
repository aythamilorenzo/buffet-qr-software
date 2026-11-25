# PLAN.md — Project State & Roadmap

## 1. Final Objective (Commercial MVP)
Web-based QR ordering system for *all-you-can-eat à la carte* restaurants:
- Table activation by waiters specifying the number of guests.
- Real-time shared table cart with individual diner identifiers (`A`, `B`, `C`...).
- Configurable per-restaurant operational rules via `RestaurantPolicy` (optional per-guest dish limit per round, optional round cooldown—disabled by default—and maximum active pending rounds in the kitchen).
- Direct kitchen output via a web Kitchen Display System (KDS) and local thermal printer (`python-escpos`), fully decoupled from external POS systems (e.g., Ágora) and with zero payment or billing handling.

## 2. Current Objective (Iteration 0: WSL Environment & GitFlow Setup) — ✅ Completed (2026-11-19)
- [x] Initialize Git repository with GitFlow branches (`main` and `develop`) and a clean `.gitignore` (Python, Node, `.env`).
- [x] Install all the dependencies required to develop the project in this WSL environment (Python 3.14.4 venv, Node 22 / npm 9, PostgreSQL 18.6 server running).
- [x] Set up `/backend` Python 3.11+ environment in WSL (`backend/pyproject.toml` with `fastapi`, `sqlmodel`, `asyncpg`, `python-escpos`, `pytest`, `ruff`) and scaffold the hexagonal folder layout (`domain/`, `application/`, `ports/`, `adapters/inbound`, `adapters/outbound`, `tests/`).
- [x] Set up `/frontend` Vite + React 19 + strict TypeScript + Tailwind CSS v4 scaffold (`tsc -b && vite build` and `oxlint` verified green).

## 3. Current Objective (Iteration 1: Backend Hexagonal Core) — in progress
- [x] Implement pure domain entities (`TableSession`, `CartItem`, `OrderRound`, `RestaurantPolicy`) in `backend/app/domain/` as frozen kw-only dataclasses with value objects (`DinerIdentifier`) and domain exceptions (zero framework imports).
- [x] Define abstract ports (`abc.ABC`: `SessionRepositoryPort`, `OrderRepositoryPort`, `KitchenNotifierPort`) in `backend/app/ports/`.
- [x] Write 55 pure domain unit tests in `backend/tests/domain/` (ruff and pytest green, no live PostgreSQL).
- [ ] Implement validation use cases in `backend/app/application/` with no hardcoded buffet constants (all rules evaluated against `RestaurantPolicy`): 6 of 7 implemented on branch `feat/use-cases` (all except `SubmitOrderRoundUseCase`).
- [ ] Write use-case tests in `/backend/tests` using in-memory fake adapters implementing the ports (no live PostgreSQL): 21 tests green with in-memory fakes (76 total); submit tests pending with the use case.
- **Mandatory Checkpoint (open 2026-11-25):** (1) confirm the port change — `OrderRepositoryPort.mark_round_completed` now returns `OrderRound` instead of `None` so the KDS notification carries the stored state; (2) decide the round composition — only the submitting diner's pending items, or the whole table's pending cart.
- **Mandatory Checkpoint (approved 2026-11-25):** Seat cap lives in `RestaurantPolicy.max_diners_per_table` (14 configured per restaurant); cooldown is per table session measured from the last round's `submitted_at` with `None` = disabled; rounds snapshot their cart lines; `RoundStatus` stays `PENDING`/`COMPLETED`; the frontend persists the diner letter. Domain branch merged into `develop` (see ADR-005 and ADR-006).

## 4. Agent Workflow & Mandatory Checkpoints
1. **Plan Before Writing:** Before creating or modifying files, briefly list the target files and their purpose. Wait for human approval if the change affects ports, database schemas, or API contracts.
2. **One Feature per Session:** Focus strictly on the *Current Objective* defined above.
3. **Mandatory Checkpoints (When to Stop & Ask):** Pause and request human review whenever:
   - A **Port** (`abc.ABC`) or database schema is defined or modified.
   - A checklist milestone under *Current Objective* is completed.
   - Any ambiguity arises regarding buffet business rules.
4. **Session Handover:** Update this `PLAN.md` with newly created files, checked-off items, and the updated *Current Objective* before concluding the session.
5. **Branch Naming:** Working branches use descriptive names without iteration numbers (e.g., `feat/env-setup`, `fix/websocket-reconnect`, `feat/domain-entities`), always created from `develop`.

## 5. References & Key Artifacts
- **Global Rules:** [AGENTS.md](./AGENTS.md)
- **Backend Context:** [backend/AGENTS.md](./backend/AGENTS.md)
- **Frontend Context:** [frontend/AGENTS.md](./frontend/AGENTS.md)
- **Backend Environment:** [backend/pyproject.toml](./backend/pyproject.toml) — editable install at `backend/.venv` (ruff line-length 88, pytest `asyncio_mode = auto`)
- **Backend Package Layout:** `backend/app/{domain,application,ports,adapters/{inbound,outbound}}`
- **Domain Layer:** `backend/app/domain/{table_session,cart_item,order_round,restaurant_policy,value_objects,exceptions}.py`
- **Ports:** `backend/app/ports/{session_repository,order_repository,kitchen_notifier}.py`
- **Domain Tests:** `backend/tests/domain/test_{table_session,cart_item,order_round,restaurant_policy,value_objects}.py`
- **Frontend Scaffold:** `frontend/vite.config.ts` (React + Tailwind v4 plugins), `frontend/tsconfig.app.json` (`"strict": true`), `frontend/src/{App.tsx,main.tsx,index.css}`
- **Active Contracts / Schemas:** *(Will be linked here as created, e.g., `backend/app/ports/` or `openapi.json`)*