# Cold Chain architecture notes

This directory contains the architecture we propose to build. These documents are design notes; they do not describe functionality already implemented unless explicitly stated.

## Documents

- [Backend architecture](backend-architecture.md): Django domain model, class diagram, API, permissions, incident lifecycle, and operational requirements.
- [Backend implementation plan](backend-implementation-plan.md): proposed branch, implementation sequence, agent task breakdown, and merge checks.
- [Progress checkpoint](progress.md): current implementation status, verified sensor flow, checkpoint commit, and next Agent task.

## Current starting point

The project now has an authenticated sensor ingestion foundation in `monitoring/`, a custom email-based user in `accounts/`, and ESP8266 firmware in `firmware/esp8266-dht11/`. The older `DHT.Dht11` model and routes remain for compatibility. The current `/dashboard/` template still reads `/api/get` and therefore the old `Dht11` table; new sensor records are visible in Django admin under **Monitoring → Measurements** until the dashboard is updated.
