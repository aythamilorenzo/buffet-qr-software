# AGENTS.md — QR Ordering System for All-You-Can-Eat Buffets

## 1. Project Description & Scope
Web application to manage table orders in *all-you-can-eat à la carte* restaurants via per-table QR codes.
- **Core Flow:** A waiter activates a table specifying the guest count -> diners scan the QR code and join a real-time shared cart with individual identifiers (`A`, `B`, `C`...) -> diners submit order rounds governed by configurable per-restaurant rules (`RestaurantPolicy`: per-guest dish limits, optional round cooldown, and max pending rounds) -> the kitchen receives the ticket on a Kitchen Display System (KDS) or thermal printer.
- **Strict Boundary (Out of Scope):** This system does NOT process payments, calculate monetary bills, issue fiscal receipts, or integrate with external POS systems (e.g., Ágora). It exclusively manages internal operational food orders routed to the kitchen.

## 2. Tech Stack
- **Backend (`/backend`):** Python 3.11+, FastAPI, SQLModel, PostgreSQL (`asyncpg`), native WebSockets, and `python-escpos`.
- **Frontend (`/frontend`):** React, strict TypeScript, Vite, Tailwind CSS, and shadcn/ui.

## 3. Module Context Rules (Mandatory Reading)
To keep the context window lean, this file contains global rules only. **Before creating, modifying, or reviewing code in either module, you must read its specific instruction file:**
- For server, database, WebSocket, or printing tasks: read [backend/AGENTS.md](./backend/AGENTS.md)
- For UI, component, or client-state tasks: read [frontend/AGENTS.md](./frontend/AGENTS.md)
- **Communication Language:** Always communicate, explain plans, and ask for checkpoint approvals in **Spanish**, while keeping all code, docstrings, commits, and documentation files in **English**.

## 4. Architecture & Design Principles
- **Hexagonal Architecture (Ports & Adapters) & Dependency Inversion:**
  - *Isolated Core (`domain/` and `application/`):* Contains exclusively entities, business rules, and use cases in pure Python. Never import `fastapi`, `sqlmodel`, `asyncpg`, or `escpos` here.
  - *Ports (`ports/`):* The core defines explicit contracts via abstract base classes (`abc.ABC` with `@abstractmethod`), such as `SessionRepositoryPort`, `OrderRepositoryPort`, or `KitchenNotifierPort`. Adapters must explicitly inherit from these ports.
  - *Adapters (`adapters/`):* Concrete technologies implement these ports (e.g., `PostgresOrderRepository` using SQLModel/asyncpg, `EscposPrinterAdapter` using `python-escpos`, or HTTP/WebSocket routers in FastAPI). Replacing the database or kitchen output medium must never require modifying the core.
- **Frontend / Backend Separation:** All business logic (round limit calculations, timer validation, concurrency control, and table state) resides exclusively in `/backend`. The frontend only renders state and dispatches user actions.
- **SOLID & DRY Principles:**
  - *Single Responsibility Principle (SRP):* Every module, class, or function must have one single reason to change. Always separate HTTP/WS routing, business logic (use cases/services), and data access (repositories/models). If a function performs two distinct behaviors, split it into two functions.
  - *Dependency Inversion Principle (DIP):* Business layers depend on abstractions/ports, never on concrete infrastructure details (such as printer drivers or HTTP transport).
  - *Don't Repeat Yourself (DRY):* Extract shared validations and schemas instead of duplicating logic across endpoints or views.

## 5. Clean Code Standards & Conventions
- **Strict Language-Native Conventions:**
  - *Python (`/backend`):* Strict PEP 8 compliance (4-space indentation, max line length <= 88 characters), `snake_case` for functions/variables/modules, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants, and mandatory static `type hints` on all function parameters and return values.
  - *TypeScript & React (`/frontend`):* Strict mode (`"strict": true`, `any` is strictly forbidden), 2-space indentation, consistent semicolons, and single quotes. Use `PascalCase` for React component files and names (e.g., `SharedCartDrawer.tsx`), `camelCase` for functions, variables, and custom hooks (`useTableWebSocket.ts`), and explicit interfaces (`interface Props`) for all component props. Use functional components with Hooks exclusively (class components are forbidden) and extract reusable or complex state logic into custom hooks.
- **Self-Explanatory Naming:** Use descriptive, context-accurate English names for variables, functions, classes, and files that reveal intent without ambiguity (e.g., `max_dishes_per_round` instead of `limit` or `n`). Anyone unfamiliar with the project must understand what the system does simply by reading the names.
- **No Inline Comments:** Inline comments (`# ...` or `// ...`) inside function bodies are strictly forbidden. If a code block requires explanation, refactor it by extracting a clearly named function.
- **Intent Documentation (Docstrings / JSDoc):** Documentation headers are allowed only on modules, classes, or complex public functions, and must explain the *what* and *why* at the domain level in natural language so they are completely understandable without reading the underlying code.

## 6. State Management & Cross-Session Continuity (`PLAN.md`)
To prevent context saturation and enable parallel feature sessions, the live project state resides in [PLAN.md](./PLAN.md):
- **At the start of every session:** Read `PLAN.md` before making any changes to understand the current objective, past decisions, and active references.
- **Upon completing a task or reaching a checkpoint:** Update `PLAN.md` by checking off completed items, updating the next current objective, registering new key contracts/files under *References*, and stop to request human confirmation before proceeding to the next step.
- **Architectural Decisions (`DECISIONS.md`):** Do NOT read `DECISIONS.md` at session startup. Only append a concise entry (max 5 lines) when a major architectural or contract decision is approved, or read it when explicitly asked why a past decision was made.

## 7. Version Control (GitFlow & Conventional Commits)
To prevent conflicts across parallel sessions and maintain a clean commit history, strictly follow **GitFlow** and **Conventional Commits**:
- **Main Branches:** `main` (stable production-ready code) and `develop` (base integration branch). Never commit directly to `main` or `develop`.
- **Working Branches:** Always branch off `develop` for each isolated task or session using prefixes `feat/<name>`, `fix/<name>`, `refactor/<name>`, or `docs/<name>`.
- **Releases (`release`):** Once a set of features in `develop` is validated for deployment, create a `release/vX.Y.Z` branch to stabilize and merge it into both `main` (tagged `vX.Y.Z`) and back into `develop`.
- **Atomic Commits:** Each commit must represent a single, complete, and functional logical change. Write commit messages in the **imperative mood, concise (<= 50 characters)**, using standard prefixes (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`). Example: `feat: add restaurant policy domain entity`.