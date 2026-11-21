# Cold Chain architecture notes

This directory contains the architecture we propose to build. These documents are design notes; they do not describe functionality already implemented unless explicitly stated.

## Documents

- [Backend architecture](backend-architecture.md): Django domain model, class diagram, API, permissions, incident lifecycle, and operational requirements.
- [Backend implementation plan](backend-implementation-plan.md): proposed branch, implementation sequence, agent task breakdown, and merge checks.

## Current starting point

The repository currently has a small Django/DRF prototype in `DHT`, with a `Measurement`-like model, SQLite, and the legacy `/api/get` and `/api/post` routes. The backend proposal describes the next version and should be implemented incrementally. Existing routes can be kept temporarily as compatibility aliases while devices are migrated to the versioned ingestion endpoint.
