# Changelog

## PAP-RFC-001-rev2.1 — 2025-11-01

- Envelope: added `trace_id` and `span_id` for OpenTelemetry correlation (proto + SDK types).
- README: clarified heartbeat is liveness-only; added DNS topology; added error code summary; added observability note.
- RFC: added rev2.1 document with DNS delegation, tracing, and heartbeat semantics.
- Examples: added separate heartbeat and metrics examples for Python and TypeScript.
- Tooling: added `Makefile` and `proto/buf.yaml`.
- Governance: added `CODE_OF_CONDUCT.md` and `SECURITY.md`; referenced in README.

## Earlier
- Scaffolding for PAP v1 transport, message families, and docs.

