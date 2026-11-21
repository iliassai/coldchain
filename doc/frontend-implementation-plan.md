# Frontend implementation plan

**Status:** Planning only; real API integration waits for [the readiness gate](frontend-readiness.md).
**Target:** React + TypeScript + Vite + shadcn/ui.
**Frontend branch:** `feat/cold-chain-frontend-v1`, created from the current backend branch for mock UI work; merge/rebase the API-ready backend before live integration.

**Repository layout recommendation:** keep the web app in `frontend/` in this repository so backend, API contract, firmware, and frontend changes can be reviewed together. Run/build the React app separately from Django; the browser talks to Django only through `/api/v1/`.

## Work that can start before backend readiness

1. Scaffold the React/Vite TypeScript app in `frontend/` (or a separately agreed frontend repository).
2. Establish Tailwind and shadcn/ui, routing, layout, accessible navigation, loading/error/empty states, and theme tokens.
3. Build page components with typed mock fixtures and a fake API adapter: login shell, refrigerator overview, temperature history, incident list/detail, acknowledgement/comment forms.
4. Keep fixture data behind an `ApiClient` interface. Do not hardcode thresholds, role authorization, escalation state, or incident lifecycle in components.
5. Prepare component tests and responsive behavior. Don’t add screens for notification settings, CSV, or user management until their backend contracts exist.

This phase can use mock data and must be labeled as not connected to live monitoring data.

### Mock-only Agent prompt (can start now)

Suggested branch: **`feat/cold-chain-frontend-v1`**, based on the current implementation branch. Suggested commit: **`feat: scaffold React monitoring frontend`**.

> Scaffold the Cold Chain web UI in `frontend/` using React, TypeScript, Vite, and shadcn/ui. Read the frontend readiness and implementation plans first. Build only the app shell, responsive navigation, and static/mock-data screens for refrigerator overview, temperature history, incident list/detail, and acknowledgement/comment states. Use typed fixtures behind an API client interface so the real backend can replace them later. Do not call current Django routes, invent final API contracts, implement business rules, or add notification/export/user-management screens. Include component tests for loading, empty, error, and mock-data states, plus lint/typecheck/build scripts. Document how to run the mock UI and clearly label it as not connected to live data. Report changed files, commands run, and remaining assumptions.

## Work after the readiness gate

1. Create `feat/cold-chain-frontend-v1` from the backend commit that passes `frontend-readiness.md`.
2. Configure the development proxy/auth behavior from the backend contract; implement real login/logout and current-user loading.
3. Replace mock adapters with typed API calls for refrigerators, latest readings, measurement history, incidents, acknowledgement, and comments.
4. Implement operator views: overview, refrigerator detail/history, open incidents, incident timeline, acknowledgement, and comment entry.
5. Apply role-based navigation for usability, while relying on backend authorization for security.
6. Add retry/empty/loading/error states and refresh behavior that does not create noisy polling. Prefer a documented refresh interval or explicit refresh; align any live updates with the backend’s 20-minute sensor cadence.
7. Integrate CSV/history or configuration screens only after those APIs are implemented and authorized.

## Suggested first frontend Agent task after readiness

Suggested commit message: **`feat: scaffold React monitoring frontend`**.

### Agent prompt

> Implement the first Cold Chain web frontend slice on `feat/cold-chain-frontend-v1`. Read `doc/frontend-readiness.md`, `doc/frontend-implementation-plan.md`, and the latest backend progress checkpoint before coding. Use React, TypeScript, Vite, and shadcn/ui. Build the app shell and operator monitoring views using the stable `/api/v1/` contract: sign in, current-user/role display, refrigerator latest readings, open incident list, incident detail/timeline, acknowledgement, and comments.
>
> Keep network calls in a typed API client, provide loading/empty/error states, and use the documented auth/CSRF or token strategy. Enforce only presentation-level role navigation in React; the backend remains authoritative for permissions. Do not add notification scheduling, push, CSV, user administration, or business rules in the client. Include component tests for rendering, loading/error/empty states, role navigation, and incident actions. Run frontend lint/typecheck/tests/build and report changed files, API assumptions, and tests run.

If the readiness gate has not passed, do not use this integration prompt. Use the mock-only scaffold task instead and keep all live API assumptions isolated in fixtures/contracts.

## Frontend test and merge gate

- Unit/component tests cover main pages and user actions; mock API responses at the client boundary.
- TypeScript typecheck, lint, and production build pass.
- API contract examples/schema agree with the backend; at least one integration smoke test covers each role and a denied action.
- Responsive layout and keyboard navigation are manually checked at desktop and mobile widths.
- No device credentials, Django secrets, or real user data are stored in frontend source or fixtures.
- README documents install, local dev proxy, environment configuration, and mock/live mode.
