# frontend/AGENTS.md — Frontend Specific Rules

> **Prerequisite:** Read the root [AGENTS.md](../AGENTS.md) and [PLAN.md](../PLAN.md) before modifying any file in this directory.

## 1. Folder Structure
Organize `/frontend/src` cleanly by responsibility:
- `types/`: TypeScript interfaces matching backend Pydantic/OpenAPI schemas (`TableSession`, `CartItem`, `OrderRound`, `RestaurantPolicy`, `Dish`).
- `services/`: HTTP API client functions and native WebSocket connection manager (`tableSocketService.ts`).
- `hooks/`: Custom React hooks encapsulating WebSocket subscriptions, reconnection logic, and local UI state (`useSharedTableCart.ts`).
- `components/`: Reusable, stateless UI components built with Tailwind CSS and shadcn/ui.
- `pages/`: Top-level views corresponding to the three operational roles:
  - `ClientMenuPage.tsx` (QR diner view: menu browsing, shared cart with `A/B/C` badges, round submission).
  - `WaiterPanelPage.tsx` (Staff view: open/close tables, set guest count).
  - `KitchenKdsPage.tsx` (Kitchen Display System: live incoming rounds filtered by station, mark round completed).

## 2. Strict Architecture Boundaries
- **Zero Business Logic in Client:** Never compute whether a round limit is exceeded or enforce cooldown timers independently in React. Always rely on the state and validation errors returned by the `/backend` API and WebSocket events.
- **Resilient Real-Time Sync:** Mobile browsers frequently suspend background tabs. WebSocket hooks must implement automatic reconnection and fetch the latest table session state upon reconnecting.
- **Mobile-First UX (`ClientMenuPage`):** Design for `375px` viewport widths first with large touch targets (`min-h-11`) for one-handed ordering.

## 3. TypeScript & React Standards
- **Strict Typing:** `"strict": true` must remain enabled. Never use `any`, `@ts-ignore`, or non-null assertions (`!`) without explicit guards.
- **Components & Hooks:** Use functional components exclusively with explicit `interface Props`. Keep JSX clean by extracting state and side effects into custom hooks.
- **Style:** 2-space indentation, single quotes, semicolons, `PascalCase` for components, `camelCase` for hooks/functions/variables, JSDoc only on complex hooks/services, and zero inline comments.