# Cold Chain implementation snapshot

**Implementation branch:** `feat/cold-chain-backend-v1`
**Latest verified checkpoint:** `a2ca15f fix: stop legacy dashboard polling during backend development`

This snapshot lives on the planning branch. The implementation commits are on `feat/cold-chain-backend-v1`; switch to that branch for executable backend or firmware code.

## Current status

- Django has a custom email-based user with roles, refrigerator/sensor/threshold models, hashed sensor credentials, and measurements.
- The ESP8266 posts to `/api/post` using device authentication and idempotency. A successful sensor request returned `201`, and readings appeared under Django admin → Monitoring → Measurements.
- The firmware defaults to a 20-minute sampling interval. Test offsets are disabled by default.
- `/dashboard/` is a static development page and does not poll `/api/get`; real dashboard integration is not implemented.
- The local implementation uses `db-v2.sqlite3`. The original `db.sqlite3` was left untouched. Legacy `Dht11` rows have not been imported.
- Backend checks and 17 tests passed at the last implementation checkpoint. PythonAnywhere has not been updated.

## Backend next step

Continue on `feat/cold-chain-backend-v1` with temperature incident creation and resolution. The detailed Agent prompt is in [backend-implementation-plan.md](backend-implementation-plan.md); its scope ends before notifications or frontend work.

## Frontend timing summary

- **Can start now:** React shell, navigation, visual exploration, and reusable components using mock data. This work must not assume the API/auth contract is finished.
- **Can integrate against the real backend after the readiness gate:** incident lifecycle plus human authentication/role endpoint, measurement/read endpoints, incident endpoints, permission rules, and a versioned API schema have been implemented and tested.
- **Does not need to block the first frontend release:** durable notification scheduling, mobile push, CSV exports, and the native app, provided the web UI clearly reflects only implemented capabilities.

See [frontend-readiness.md](frontend-readiness.md) for the gate checklist and [frontend-implementation-plan.md](frontend-implementation-plan.md) for tasks and Agent prompts. Mock-only UI work can start now; real API integration waits for the gate.
