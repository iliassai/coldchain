# Cold Chain architecture notes

This directory contains the architecture we propose to build. These documents are design notes; they do not describe functionality already implemented unless explicitly stated.

## Documents

- [Backend architecture](backend-architecture.md): Django domain model, class diagram, API, permissions, incident lifecycle, and operational requirements.
- [Backend implementation plan](backend-implementation-plan.md): proposed branch, implementation sequence, agent task breakdown, and merge checks.
- [Progress checkpoint](progress.md): current implementation status, verified sensor flow, checkpoint commit, and next Agent task.

## Current starting point

The project now has an authenticated sensor ingestion foundation in `monitoring/`, a custom email-based user in `accounts/`, and ESP8266 firmware in `firmware/esp8266-dht11/`. The older `DHT.Dht11` model and routes remain for compatibility. `/dashboard/` is currently a static development page with a link to the Django admin measurements list; new sensor records are visible under **Monitoring → Measurements**.
