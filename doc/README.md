# Cold Chain architecture notes

This directory contains the architecture we propose to build. These documents are design notes; they do not describe functionality already implemented unless explicitly stated.

## Documents

- [Backend architecture](backend-architecture.md): Django domain model, class diagram, API, permissions, incident lifecycle, and operational requirements.
- [Backend implementation plan](backend-implementation-plan.md): backend phases, Agent assignments, and merge checks.
- [Frontend readiness gate](frontend-readiness.md): the exact backend/API milestone after which React can integrate against real endpoints.
- [Frontend implementation plan](frontend-implementation-plan.md): React + shadcn/ui milestones, branch strategy, tests, and Agent prompts.
- [Progress checkpoint](progress.md): latest verified backend/sensor state and next task.

## Current starting point

The implementation status is tracked on `feat/cold-chain-backend-v1`; the last verified checkpoint is commit `a2ca15f`. That branch has authenticated sensor ingestion, persisted measurements, and a static development dashboard page. The planning branch intentionally contains architecture and sequencing docs; see [progress](progress.md) for the implementation snapshot.
