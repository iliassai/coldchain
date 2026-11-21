# Backend progress checkpoint

**Branch:** `feat/cold-chain-backend-v1`
**Checkpoint commit message:** `feat: add authenticated sensor ingestion foundation`

This checkpoint captures a working first backend slice and the first physical ESP8266-to-Django data flow. The commit should include the implementation and documentation listed here, but never the ignored local database or `firmware/esp8266-dht11/secrets.h`.

## Completed

- Added the custom email-based Django user and `ADMIN`, `OPERATOR_1`, `OPERATOR_2`, `OPERATOR_3` roles.
- Added refrigerator, sensor, hashed/revocable sensor credential, effective-dated threshold policy, and immutable measurement models with validation and database constraints.
- Added authenticated sensor ingestion at `/api/v1/ingest/measurements/` and kept `/api/post` as a secure adapter for the historical `temp`/`hum` payload. Both require idempotency identifiers.
- Added `issue_sensor_credential` for one-time provisioning. Issuing a new credential revokes the previous credential for that sensor.
- Added the ESP8266 DHT11 sketch under `firmware/esp8266-dht11/`. It sends measurements every 20 minutes by default, retries the same pending sample with the same key, and keeps secrets in ignored `secrets.h`.
- Updated setup documentation and preserved the old `DHT.Dht11` model/routes for migration compatibility.

## Verified state

- The sensor connected to Wi-Fi and received HTTP `201` responses from `/api/post`; the Django response returned saved measurement IDs.
- The Django admin **Monitoring → Measurements** list showed the sensor readings, including temperature and humidity.
- Backend verification last run: `manage.py check`, `makemigrations --check --dry-run`, and `manage.py test` (17 tests passed). Fresh SQLite migrations also applied successfully.
- `db-v2.sqlite3` is the active local database. The original `db.sqlite3` has not been migrated or modified by the new schema. Existing `Dht11` rows have not been imported.
- The PythonAnywhere deployment has not been updated; successful hardware testing was against the local development server.

## Dashboard status

`/dashboard/` is a static development page and no longer polls the legacy `/api/get` endpoint. New ingestion writes to `monitoring.Measurement`; readings are available in Django admin under **Monitoring → Measurements**. Wiring a real dashboard to current measurements is future frontend/API work and is not part of the next task below.

## Next step: temperature incident lifecycle

Next branch: continue on **`feat/cold-chain-backend-v1`**.
Suggested commit message: **`feat: detect and resolve temperature incidents`**.

### Agent prompt

> Implement the next backend phase for Cold Chain on `feat/cold-chain-backend-v1`. Read `doc/backend-architecture.md`, `doc/backend-implementation-plan.md`, and this checkpoint first. Add a temperature `Incident` model and connect incident lifecycle processing to newly created measurements in the existing ingestion service.
>
> When a newly accepted, chronologically newer measurement is below the effective threshold minimum or above its maximum, open one temperature incident for that refrigerator and link its trigger measurement and effective threshold policy. When a later, chronologically newer reading is within the inclusive range, resolve that open incident and link the resolving measurement. Equality with a threshold is in range. Idempotent replays must not reprocess transitions, and stale readings must not resolve an incident. Make creation/resolution atomic with measurement ingestion and protect against duplicate open temperature incidents under concurrent requests using an appropriate database constraint and transaction strategy.
>
> Add focused tests for below-minimum and above-maximum opening, in-range resolution, inclusive boundaries, repeated out-of-range readings, stale readings, idempotent replay, per-refrigerator threshold precedence, and duplicate prevention. Run the existing suite and checks. Do not implement acknowledgements/comments, audit events, notifications/escalation, push, CSV, or frontend/dashboard changes in this task. Preserve `/api/post` and the modern ingestion endpoint, report migration implications, changed files, tests run, and remaining decisions.

## Known follow-up work

1. Temperature incident lifecycle (next task above).
2. Incident query/timeline APIs, acknowledgements, comments, and audit events.
3. Durable notifications and level 1/2/3 escalation.
4. Measurement/dashboard read API and frontend integration; the current dashboard is legacy.
5. Decide whether and how to import legacy `Dht11` data and deploy the new schema to PythonAnywhere.
6. PostgreSQL integration tests for concurrency-sensitive constraints before production deployment.
