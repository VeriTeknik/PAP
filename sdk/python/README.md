# PAP Python SDK

Python tooling for connecting Satellites to the Station, managing handshakes, and streaming telemetry.

## Goals
- gRPC client with automatic certificate loading and retry helpers.
- Dataclass representations of PAP envelopes mirroring `proto/pap/v1/pap.proto`.
- Async heartbeat scheduler with pluggable probes.
- CLI utilities for local agent development and debugging.

## Development Setup
```
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Code generation hooks will land under `pap/gen` when protobuf compilation is wired in.
