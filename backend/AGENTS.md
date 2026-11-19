# backend/AGENTS.md — Backend Specific Rules

> **Prerequisite:** Read the root [AGENTS.md](../AGENTS.md) and [PLAN.md](../PLAN.md) before modifying any file in this directory.

## 1. Hexagonal Folder Structure
Strictly maintain layer boundaries inside `/backend/app`:
- `domain/`: Pure Python entities (`@dataclass(frozen=True)` where applicable), value objects, and domain exceptions (`TableSession`, `CartItem`, `OrderRound`, `RestaurantPolicy`). Zero external framework imports allowed.
- `ports/`: Abstract base classes (`abc.ABC` + `@abstractmethod`) defining repository and external notifier interfaces (`SessionRepositoryPort`, `OrderRepositoryPort`, `KitchenNotifierPort`).
- `application/`: Use cases orchestrating domain entities and ports (e.g., `OpenTableSessionUseCase`, `SubmitOrderRoundUseCase`). Depends exclusively on `domain/` and `ports/`.
- `adapters/`:
  - `inbound/`: FastAPI HTTP routers, Pydantic request/response DTOs, and native WebSocket connection managers.
  - `outbound/`: Concrete implementations inheriting explicitly from `ports/` (`PostgresSessionRepository`, `PostgresOrderRepository` using SQLModel + `asyncpg`, and `EscposPrinterAdapter` using `python-escpos`).

## 2. Domain & Business Rules
- **No Hardcoded Buffet Rules:** Every operational constraint (per-guest dish limit per round, optional round cooldown in seconds, maximum active pending rounds in kitchen) must be evaluated against the `RestaurantPolicy` domain entity. Magic numbers in use cases or routers are strictly forbidden.
- **Concurrency Safety:** Database operations that validate round limits or close sessions must use asynchronous atomic transactions (`asyncpg` / SQLModel `AsyncSession`) with row-level locking (`with_for_update()`) to prevent race conditions when multiple diners submit simultaneously.
- **Diner Identification:** Assign sequential uppercase letters (`A`, `B`, `C`...) per active table session so shared cart items remain attributable to each diner.

## 3. Code Quality & Testing
- **Async Everywhere:** All repository ports, database queries, FastAPI routes, and WebSocket handlers must use `async`/`await`. Never use synchronous blocking drivers (`psycopg2`, `time.sleep`).
- **Testing (`pytest`):** Every use case and domain rule must have fast unit tests in `/backend/tests` using in-memory fake adapters implementing `ports/` without requiring a live PostgreSQL instance.
- **Style:** Enforce PEP 8, mandatory type hints on all signatures, domain-level docstrings only, and zero inline comments.