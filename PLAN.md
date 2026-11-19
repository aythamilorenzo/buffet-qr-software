# PLAN.md — Project State & Roadmap

## 1. Final Objective (Commercial MVP)
Web-based QR ordering system for *all-you-can-eat à la carte* restaurants:
- Table activation by waiters specifying the number of guests.
- Real-time shared table cart with individual diner identifiers (`A`, `B`, `C`...).
- Configurable per-restaurant operational rules via `RestaurantPolicy` (optional per-guest dish limit per round, optional round cooldown—disabled by default—and maximum active pending rounds in the kitchen).
- Direct kitchen output via a web Kitchen Display System (KDS) and local thermal printer (`python-escpos`), fully decoupled from external POS systems (e.g., Ágora) and with zero payment or billing handling.

## 2. Current Objective (Iteration 0: WSL Environment & GitFlow Setup)
- [ ] Initialize Git repository with GitFlow branches (`main` and `develop`) and a clean `.gitignore` (Python, Node, `.env`).
- Install all the dependencies required to develop the project in this wsl environment.
- [ ] Set up `/backend` Python 3.11+ environment in WSL (`pyproject.toml` or `requirements.txt` with `fastapi`, `sqlmodel`, `asyncpg`, `python-escpos`, `pytest`, `ruff`) and scaffold the hexagonal folder layout (`domain/`, `application/`, `ports/`, `adapters/`).
- [ ] Set up `/frontend` Vite + React + strict TypeScript + Tailwind CSS scaffold.
- **Next Step (Iteration 1: Backend Hexagonal Core):** Implement pure domain entities (`TableSession`, `CartItem`, `OrderRound`, `RestaurantPolicy`), abstract ports (`abc.ABC`: `SessionRepositoryPort`, `OrderRepositoryPort`, `KitchenNotifierPort`), validation use cases without hardcoded constants, and pure Python unit tests.

## 3. Agent Workflow & Mandatory Checkpoints
1. **Plan Before Writing:** Before creating or modifying files, briefly list the target files and their purpose. Wait for human approval if the change affects ports, database schemas, or API contracts.
2. **One Feature per Session:** Focus strictly on the *Current Objective* defined above.
3. **Mandatory Checkpoints (When to Stop & Ask):** Pause and request human review whenever:
   - A **Port** (`abc.ABC`) or database schema is defined or modified.
   - A checklist milestone under *Current Objective* is completed.
   - Any ambiguity arises regarding buffet business rules.
4. **Session Handover:** Update this `PLAN.md` with newly created files, checked-off items, and the updated *Current Objective* before concluding the session.

## 4. References & Key Artifacts
- **Global Rules:** [AGENTS.md](./AGENTS.md)
- **Backend Context:** [backend/AGENTS.md](./backend/AGENTS.md) *(to be created)*
- **Frontend Context:** [frontend/AGENTS.md](./frontend/AGENTS.md) *(to be created)*
- **Active Contracts / Schemas:** *(Will be linked here as created, e.g., `backend/app/ports/` or `openapi.json`)*