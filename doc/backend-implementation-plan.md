# Backend implementation plan

**Status:** Foundation implemented; incident lifecycle is next
**Architecture reference:** [Backend architecture](backend-architecture.md)

This plan turns the backend proposal into staged, reviewable work. The first foundation is implemented on the branch below; see [progress checkpoint](progress.md) for the verified state and checkpoint commit.

## Branch

Recommended branch name: **`feat/cold-chain-backend-v1`**

This is the active implementation branch. Keep changes focused on the Django backend, sensor firmware, and their documentation. Avoid mixing native mobile UI implementation into this branch; expose and verify the API contracts those clients will use.

## Agent assignment

### Completed task: backend foundation and authenticated measurement ingestion

Give the Agent this bounded task:

> Implement the first backend foundation for Cold Chain in Django. Add a custom email-based user model and role field before creating any migrations for new domain models. Add refrigerator, sensor, threshold policy, and measurement models with the key invariants from `doc/backend-architecture.md`. Implement authenticated, idempotent sensor measurement ingestion and retain `/api/post` as a compatibility adapter to the same ingestion service. Add migrations and focused tests. Do not implement incident escalation, push notifications, CSV export, or frontend/mobile clients in this task. Report changed files, migration implications, tests run, and unresolved decisions.

This is the highest-risk foundation because Django’s custom user model is difficult to introduce after Django’s built-in auth migrations have already been applied. The repository already has a `DHT` initial migration, so the Agent must inspect `showmigrations` and determine whether the existing SQLite database is disposable or whether a migration path is needed before changing `AUTH_USER_MODEL`. Do not assume that “before new feature migrations” makes an already-migrated database safe. Also preserve existing data/API behavior where practical and avoid silently dropping legacy `Dht11` measurements. If a data migration is not safe to automate, document a manual migration path.

The work was implemented and manually verified with the ESP8266 against the local Django server. The active local database is `db-v2.sqlite3`; the original `db.sqlite3` remains untouched. Historical `Dht11` rows have not been imported.

### Next task: temperature incident lifecycle

Use the detailed Agent prompt in [progress.md](progress.md). Keep this task focused on creating and resolving temperature incidents from newly accepted measurements. Do not add notification delivery/escalation or frontend work in this phase.

## Work breakdown

Keep each task independently reviewable. The tasks can be separate commits or follow-up Agent assignments on the same branch.

### 0. Confirm implementation choices

- Confirm the target database for the implementation environment: SQLite can remain for local development; use PostgreSQL for concurrency-sensitive integration/production validation.
- Select authentication packages and token revocation behavior for the mobile client.
- Confirm email invitation/password setup, global threshold bootstrap, and whether all active operators at each level are recipients.
- Pin required dependencies in `requirements.txt` only when the corresponding feature is implemented.

### 1. Foundation, domain models, and ingestion

- Decide and document the custom-user migration strategy first; then add the custom user model, role choices, and admin setup before creating feature migrations. Use a fresh database for development if existing local data is disposable; provide a deliberate migration plan if data must be retained.
- Add refrigerator, sensor, credential, threshold policy, and measurement models.
- Add validation for threshold ranges, policy time periods, device status, timestamps, numeric bounds, and idempotency keys.
- Implement a sensor-specific credential and `/api/v1/ingest/measurements/` endpoint.
- Route the existing `/api/post` endpoint through the same service during migration; preserve a compatibility path for current device payloads.
- Add a documented data migration or export/import path for existing `Dht11` rows.

### 2. Incident lifecycle and audit

- Add incident, acknowledgement, comment, and audit event models.
- Implement atomic incident transitions from chronologically newer measurements.
- Add database/application protection against duplicate open incidents under concurrent ingestion.
- Implement role-filtered incident list/detail/timeline endpoints and operator acknowledgement/comment actions.
- Record state transitions, threshold edits, account changes, and operator actions in the audit history.

### 3. Durable escalation and notification delivery

- Add notification delivery records and the durable worker/scheduler configuration.
- Implement level 1 at incident start, level 2 at 1 hour, and level 3 at 2 hours; repeat every 20 minutes while the incident is open.
- Ensure acknowledgement does not suppress reminders or escalation.
- Persist delivery intent before sending; add retries, cancellation of unsent deliveries on resolution, and delivery result tracking.
- Implement a notification adapter interface, then add the agreed push provider and Telegram fallback if required.
- Define and implement behavior for worker downtime, recipient role changes, and ambiguous provider timeouts.

### 4. Monitoring, history, and exports

- Add bounded, paginated measurement and incident queries with date/refrigerator filters.
- Add latest-reading and dashboard summary endpoints.
- Enforce level 1/2 open-only incident visibility and level 3/admin historical access in the API itself.
- Add level 3/admin CSV exports with safe streaming and consistent filters.

### 5. Silent sensor detection and operational readiness

- Implement sensor-silent incidents only after the pending requirement is confirmed.
- Add liveness/readiness endpoints, structured logging, secrets configuration, and operational notes for backups, migrations, and credential rotation.
- Verify worker and API behavior after restart and during provider/database/queue failure conditions.

## Required tests before merge

Run the complete test suite after each task and before merge. Tests should use Django’s test runner/DRF API client and a separate PostgreSQL integration run for behavior that depends on row locking or partial unique constraints.

### Automated unit and API tests

- **Models and migrations:** user email uniqueness and roles; threshold min/max validation and non-overlapping effective periods; model relationships and deletion protection; migrations apply from an empty database and from the current schema.
- **Ingestion:** valid reading accepted; invalid/missing/out-of-range payload fields rejected; sensor credential required; credential cannot write for another sensor; revoked/inactive credentials rejected; timestamps and future-skew rules enforced; duplicate external ID/idempotency key does not create a second measurement or rerun incident processing.
- **Legacy compatibility:** current `/api/post` payload is accepted through the shared service during migration; `/api/get` response shape remains compatible until deprecation is agreed.
- **Incident lifecycle:** below-minimum and above-maximum readings open incidents; in-range newer reading resolves; acknowledgement alone does not resolve; repeated abnormal samples do not create duplicate open incidents; threshold overrides and effective dates select the right policy; stale readings do not close incidents.
- **Concurrency:** simultaneous ingestion for the same refrigerator does not create multiple open incidents. Run this test against PostgreSQL; SQLite does not validate PostgreSQL row-locking semantics.
- **Permissions:** each role can perform only allowed actions; level 1/2 cannot access resolved history or CSV exports; level 3 can access history/exports and thresholds but cannot manage users; unauthenticated and sensor-authenticated clients cannot use human-only endpoints.
- **Audit:** important user and system actions create attributable timestamped events; secrets and credential material are absent from audit metadata; operator roles cannot mutate/delete history through the API.
- **Notifications:** deterministic schedule assertions at 0, 60, 80, and 120 minutes; level 1 has five and level 2 has two sends by `t=80m`; level 3 first becomes due at `t=2h`; acknowledgement does not alter the schedule; resolved incident skips future sends; duplicate worker execution does not duplicate delivery records.
- **Failure handling:** queue publication failure leaves durable work discoverable; provider retry/failure is recorded; an ambiguous provider timeout follows the documented at-least-once behavior; worker restart recovers due tasks.
- **Exports and monitoring:** date and refrigerator filters are honored; limits/pagination apply; CSV headers/rows are correct; unauthorized export is denied; dashboard aggregates match stored measurements/incidents.
- **Silent sensor, if included:** no incident before the agreed timeout, one incident when timeout passes, no duplicates on repeated scheduler runs, and resolution after sensor recovery.

### Merge gate commands

Use the repository’s supported Python environment and run the commands that apply to the finished scope:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --check
python manage.py test
```

Also run the PostgreSQL integration test job, formatter/linter if one is adopted, and a manual API smoke test using one device credential and each human role. Do not claim PostgreSQL concurrency coverage from SQLite-only runs. Update README/setup instructions and this architecture documentation when dependencies, environment variables, routes, or migration steps change.

## Merge checklist

- [ ] Migrations apply cleanly from a fresh database and documented existing-data migration path is available.
- [ ] API permissions and device/human authentication boundaries are covered by tests.
- [ ] Incident and notification timing matches the acceptance examples in the requirements.
- [ ] PostgreSQL concurrency/integration checks pass for database-specific invariants.
- [ ] No credentials, tokens, local database files, or generated secrets are committed.
- [ ] README documents setup, worker/scheduler processes, required environment variables, and compatibility/deprecation status of old routes.
- [ ] Any unresolved stakeholder decision is recorded and does not silently change required behavior.
