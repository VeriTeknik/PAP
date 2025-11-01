# PAP Proxy

The PAP Proxy (`mcp.plugged.in`) is the entrypoint for all Satellite traffic. It terminates TLS, validates signatures, enforces rate limits, and forwards messages to the Station.

## Responsibilities
- Terminate mutual TLS and map client certificates to agent identities.
- Validate envelope signatures and payload hashes before forwarding.
- Apply policy checks (capability allowlists, quotas, throttles).
- Stream telemetry to the Plugged.in Memory service via OpenTelemetry.
- Buffer and retry deliveries to the Station within configured SLOs.

## Planned Components
- Authentication middleware (certificate + JWT onboarding support).
- gRPC interceptors for logging, traces, and metrics.
- Policy engine integrating with the Registry service.
- Dead-letter queue for rejected messages.

Implementation artifacts (Helm charts, Dockerfiles) will land once the service design is finalized.
