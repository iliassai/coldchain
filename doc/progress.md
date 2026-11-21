# Cold Chain implementation checkpoint

**Implementation branch:** `feat/cold-chain-backend-v1`
**Latest verified implementation checkpoint:** `a2ca15f fix: stop legacy dashboard polling during backend development`

This snapshot records the backend implementation and the local sensor flow. The executable backend and firmware are in this branch. See [sensor-onboarding.md](sensor-onboarding.md) for repeatable local setup and device provisioning.

## Completed

- Added the custom email-based Django user and `ADMIN`, `OPERATOR_1`, `OPERATOR_2`, and `OPERATOR_3` roles.
- Added refrigerator, sensor, hashed/revocable sensor credential, effective-dated threshold policy, and immutable measurement models with validation and database constraints.
- Added authenticated sensor ingestion at `/api/v1/ingest/measurements/` and kept `/api/post` as a secure adapter for the historical `temp`/`hum` payload. Both require idempotency identifiers.
- Added `issue_sensor_credential` for one-time provisioning. Issuing a new credential revokes the previous credential for that sensor.
- Added the ESP8266 DHT11 sketch under `firmware/esp8266-dht11/`. It sends measurements every 20 minutes by default, retries the same pending sample with the same key, and keeps secrets in ignored `secrets.h`.
- Preserved the old `DHT.Dht11` model/routes for migration compatibility.

## Verified state and migration notes

- The sensor connected to Wi-Fi and received HTTP `201` responses from `/api/post`; readings appeared in Django admin → **Monitoring → Measurements**.
- `/dashboard/` is a static development page and does not poll `/api/get`.
- Backend checks, migrations, and 17 tests passed at the last implementation checkpoint. PythonAnywhere has not been updated.
- The local implementation uses `db-v2.sqlite3`; the original `db.sqlite3` was left untouched. Legacy `Dht11` rows have not been imported.

## Next backend task

Continue on `feat/cold-chain-backend-v1` with temperature incident creation and resolution. Suggested commit message: **`feat: detect and resolve temperature incidents`**.

### Agent prompt

> Implement the next backend phase for Cold Chain on `feat/cold-chain-backend-v1`. Read `doc/backend-architecture.md`, `doc/backend-implementation-plan.md`, and this checkpoint first. Add a temperature `Incident` model and connect incident lifecycle processing to newly created measurements in the existing ingestion service.
>
> When a newly accepted, chronologically newer measurement is below the effective threshold minimum or above its maximum, open one temperature incident for that refrigerator and link its trigger measurement and effective threshold policy. When a later, chronologically newer reading is within the inclusive range, resolve that open incident and link the resolving measurement. Equality with a threshold is in range. Idempotent replays must not reprocess transitions, and stale readings must not resolve an incident. Make creation/resolution atomic with measurement ingestion and protect against duplicate open temperature incidents under concurrent requests using an appropriate database constraint and transaction strategy.
>
> Add focused tests for below-minimum and above-maximum opening, in-range resolution, inclusive boundaries, repeated out-of-range readings, stale readings, idempotent replay, per-refrigerator threshold precedence, and duplicate prevention. Run the existing suite and checks. Do not implement acknowledgements/comments, audit events, notifications/escalation, push, CSV, or frontend/dashboard changes in this task. Preserve `/api/post` and the modern ingestion endpoint, report migration implications, changed files, tests run, and remaining decisions.

## Frontend timing

- **Can start now:** React shell, navigation, visual exploration, and reusable components using mock data. Do not assume the API/auth contract is finished.
- **Can integrate against the real backend after the readiness gate:** incident lifecycle, human authentication/role endpoint, measurement/read endpoints, incident endpoints, permission rules, and a versioned API schema have been implemented and tested.
- Durable notification scheduling, mobile push, CSV exports, and the native app do not need to block an initial frontend release if the UI only shows implemented capabilities.

See [frontend-readiness.md](frontend-readiness.md) for the gate checklist and [frontend-implementation-plan.md](frontend-implementation-plan.md) for milestones and Agent prompts. Mock-only UI work can start now; real API integration waits for the gate.

## Later work

1. Incident query/timeline APIs, acknowledgements, comments, and audit events.
2. Durable notifications and level 1/2/3 escalation.
3. Measurement/dashboard read API and frontend integration; the current dashboard is static.
4. Decide whether and how to import legacy `Dht11` data and deploy the new schema to PythonAnywhere.
5. PostgreSQL integration tests for concurrency-sensitive constraints before production deployment.
