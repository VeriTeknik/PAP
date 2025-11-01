# PAP Operations

Operational runbooks, SLO definitions, and incident response guides for Plugged.in Agent Protocol deployments will live in this directory.

## Initial Focus Areas
- **Heartbeat SLOs:** Define target intervals, grace periods, and escalation paths.
- **Kill Authority Playbooks:** Document approval workflows and audit requirements before triggering `force_kill`.
- **Telemetry Pipelines:** Outline OpenTelemetry exporter configuration, retention, and replay processes.
- **Disaster Recovery:** Capture snapshot/restore procedures for Registry state and Proxy routing tables.

## TODO
- Draft heartbeat policy templates aligned with `docs/rfc/pap-rfc-001.md`.
- Document rollout/rollback steps for protocol version upgrades.
- Establish observability dashboards and alert thresholds.
