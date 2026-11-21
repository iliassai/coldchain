# Cold Chain architecture notes

This directory contains the architecture we propose to build. These documents are design notes; they do not describe functionality already implemented unless explicitly stated.

## Documents

- [Backend architecture](backend-architecture.md): Django domain model, class diagram, API, permissions, incident lifecycle, and operational requirements.
- [Backend implementation plan](backend-implementation-plan.md): backend phases, Agent assignments, and merge checks.
- [Frontend readiness gate](frontend-readiness.md): the backend/API milestone after which React can integrate against real endpoints.
- [Frontend implementation plan](frontend-implementation-plan.md): React + shadcn/ui milestones, branch strategy, tests, and Agent prompts.
- [Sensor onboarding](sensor-onboarding.md): repeatable local setup, sensor registration, credential provisioning, firmware configuration, and verification.
- [Progress checkpoint](progress.md): verified backend/sensor state, frontend timing, and next backend task.

## Current starting point

The active implementation branch is `feat/cold-chain-backend-v1`. It has authenticated sensor ingestion, persisted measurements, and ESP8266 firmware; the older `DHT.Dht11` model and routes remain for compatibility. `/dashboard/` is currently a static development page; new sensor records are visible under Django admin → **Monitoring → Measurements**. See [progress](progress.md) for the verified checkpoint and [sensor onboarding](sensor-onboarding.md) for repeatable device setup.
