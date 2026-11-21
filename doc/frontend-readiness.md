# Frontend readiness gate

**Frontend stack target:** React + TypeScript + Vite, with shadcn/ui components.
**Backend implementation branch:** `feat/cold-chain-backend-v1`
**Purpose:** Define when the frontend can use real backend data rather than mocks.

## Short answer

Frontend visual work can start now against mock data. The backend is **not yet ready for real frontend integration**: it currently accepts sensor measurements and exposes them in Django admin, but it has no human login/API identity, no measurement read API, and no incident API.

The frontend can switch from mocks to the real backend once all readiness checks below pass. It does not need to wait for mobile push or notification escalation.

## Readiness checks

### 1. Human identity and authorization contract

- A browser login/session flow is implemented and tested. Decide whether the React web app uses Django session + CSRF (recommended for a same-site web app) or a token flow before integration.
- `GET /api/v1/users/me/` returns a stable user ID, role, and the fields the UI needs.
- Role permissions are enforced server-side and documented. At minimum, level 1/2 must not gain level 3 history/export capabilities through direct API calls.
- CORS/CSRF and local-development proxy behavior are documented for the chosen deployment topology.

### 2. Read contracts needed by the first operator UI

- Refrigerator list/detail returns identity, active state, effective threshold, latest temperature/humidity, and last-seen age.
- Measurement history is filterable by refrigerator and bounded date range, with stable ordering and pagination or an explicit chart-series response.
- Incident list/detail/timeline responses and state/status fields are defined and implemented.
- Acknowledgement and comment writes have stable request/response shapes and permission behavior.
- Threshold and user-management APIs are defined separately if those screens are in the first web scope; Django admin can remain the initial system-management UI.

The endpoint names should follow `backend-architecture.md` unless a reviewed API contract updates that document. Avoid building a frontend against endpoint names inferred from Django admin routes.

### 3. Contract and developer experience

- API remains under `/api/v1/`; errors, timestamps, pagination, and filtering behavior are documented consistently.
- An OpenAPI schema or equivalent checked-in API contract includes request/response examples for login, current user, monitoring, incidents, acknowledgement, and comments.
- Local setup provides a fresh database, seeded refrigerator/sensor/threshold, and test accounts for every role without real credentials.
- Backend API tests cover happy paths and permission failures. The schema/contract check runs in CI or is included in the merge checklist.
- The frontend can run against the local API through a documented Vite proxy or same-origin dev setup.

## Gate decision

Mark frontend integration **READY** only when all three sections pass. The UI may still be implemented before then with mock fixtures, but it must isolate mock data behind an API client so swapping to live endpoints does not require rewriting components.

First frontend integration slice after readiness: sign in, show current operator role, list refrigerators/latest readings, display open incidents, and open incident detail. Add acknowledgement/comments once those endpoints are ready. Keep notification preferences, export, and user management outside this first slice unless their APIs are also complete.

## Current gate status

**NOT READY for real API integration.** Current backend has sensor ingestion only. Next backend work is incident lifecycle, then human auth and the read/action endpoints listed above. UI shell and mock-data components can begin in parallel now.
