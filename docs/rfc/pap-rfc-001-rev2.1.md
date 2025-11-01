# PAP-RFC-001 — Plugged.in Agent Protocol rev2.1

- Status: Stable candidate (rev2.1)
- Version: PAP-RFC-001-rev2.1
- Audience: Plugged.in Core, Satellite developers, infrastructure team

This revision aligns the repository and protocol with observability, DNS/infra, and governance expectations for PAP rev2.1. It formalizes tracing identifiers in the envelope, clarifies heartbeat as a liveness-only signal, and documents DNS delegation for the Proxy and Agent subzones.

## 1. Transport & Identity

1. HTTP/2 over TLS 1.3 with mutual authentication.
2. gRPC is the canonical binding; alternatives must preserve semantics.
3. Default endpoint: `pap.plugged.in:443`, regional: `{region}.pap.plugged.in`.
4. Onboarding uses short-lived JWT invite tokens → long-lived client certificates.
5. DNS identity: `{agent}.{cluster}.a.plugged.in` with DNSSEC; SANs must match.

## 2. DNS Topology

- Base: `plugged.in`
- Proxy: `mcp.plugged.in` (TLS termination, routing, rate limiting)
- Agents: `a.plugged.in` delegated to cluster DNS; agent FQDNs are `{agent}.{cluster}.a.plugged.in`
- Stream Gateway: long-lived bidi streams (gRPC) terminate at the Proxy and are routed by identity and capability.

## 3. Envelope & Observability

Every PAP message is wrapped in an envelope carrying audit and correlation fields.

Required fields:
- `message_id` (UUIDv7), `sent_at`, `sender`, `auth`, `body`

Recommended/optional:
- `parent_id`, `correlation_id`, `annotations`
- `trace_id`, `span_id` (OpenTelemetry-compatible; 16-byte/8-byte hex strings)

Signing:
- Ed25519 recommended. Signature covers a canonical header + body representation.
- Proxy rejects unsigned or invalid signatures with `UNAUTHORIZED`.

Tracing:
- Proxies MUST propagate and emit traces keyed by `trace_id`/`span_id`.
- Stations SHOULD link spans for `invoke` → `response` causality.
- Satellites SHOULD map handler spans to the envelope’s `trace_id`/`span_id`.

## 4. Message Families

- `invoke`: commands; must ack or complete within negotiated timeouts.
- `response`: results; may stream; final chunk sets `is_final = true`.
- `event`: telemetry; subtypes: `HEARTBEAT`, `LOG`, `ALERT`, `METRIC`.
- `error`: structured failures; includes `code`, `message`, `recoverable`, `details`.
- `control`: lifecycle directives (`terminate`, `force_kill`, `pause`, `resume`, `ping`).
- `handshake_ack`: agent acknowledgement after applying bootstrap config.

## 5. Heartbeat (Liveness Only)

- Heartbeat indicates liveness, not readiness. It must not gate task acceptance.
- Payload: `cpu_percent`, `memory_mb`, `uptime_seconds`, `active_jobs`, optional `gauges`.
- Default interval: 10s. Unhealthy after 3 consecutive misses ⇒ `AGENT_UNHEALTHY`.
- Business/perf metrics are separate `event.metrics` batches.

## 6. Error Codes

| Enum | HTTP | Description |
|------|------|-------------|
| `OK` | 200 | Success |
| `ACCEPTED` | 202 | Async acceptance |
| `BAD_REQUEST` | 400 | Invalid message or args |
| `UNAUTHORIZED` | 401 | Missing/invalid credentials |
| `FORBIDDEN` | 403 | Policy denied |
| `NOT_FOUND` | 404 | Target or method missing |
| `TIMEOUT` | 408 | Job/agent timeout |
| `CONFLICT` | 409 | Version/concurrency conflict |
| `RATE_LIMITED` | 429 | Quota exceeded |
| `AGENT_UNHEALTHY` | 480 | Heartbeat anomaly |
| `AGENT_BUSY` | 481 | Overloaded; retry later |
| `DEPENDENCY_FAILED` | 482 | Downstream failure |
| `INTERNAL_ERROR` | 500 | Agent fault |
| `PROXY_ERROR` | 502 | Routing/connection issue |
| `VERSION_UNSUPPORTED` | 505 | Protocol mismatch |

## 7. Lifecycle

- Provisioning: token → certificate, DNS entry, policy baseline.
- Ownership transfer: dual-homing with state snapshot/stream, revocation on cutover.
- Termination: graceful `terminate` vs `force_kill` with certificate revocation.

## 8. Compliance (rev2.1)

- Envelope carries `trace_id` and `span_id` fields.
- Heartbeat semantics treated as liveness-only.
- DNS topology and delegation documented and implemented.
- Proxy emits OpenTelemetry spans linking requests and results.

## 9. Changelog (rev2.1)

- Added `trace_id`/`span_id` to the envelope for end-to-end tracing.
- Clarified heartbeat liveness-only semantics and metrics separation.
- Documented DNS delegation across `mcp.plugged.in` and `a.plugged.in`.
- Introduced governance docs references (security and conduct).

