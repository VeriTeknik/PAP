# PAP Registry & Policy Layer

The Registry service maintains authoritative records for Satellite identities, capabilities, lifecycle policies, and access rules enforced by the Station and Proxy.

## Scope
- Persist agent metadata (DNS labels, clusters, attestations).
- Manage capability declarations and compatibility checks.
- Store lifecycle policies (heartbeat thresholds, kill authority, escalation plans).
- Issue and rotate onboarding tokens and certificates.
- Provide audit APIs for external governance tooling.

## Initial Design Thoughts
- Backed by a strongly consistent datastore (e.g., PostgreSQL or CockroachDB).
- API surface exposed via gRPC and REST gateways.
- Policy evaluation via Rego or in-process rules engine.
- Event sourcing for long-term audit and replication.

Future milestones will add schema migrations, API contracts, and deployment automation.
