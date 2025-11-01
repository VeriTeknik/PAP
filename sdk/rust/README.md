# PAP Rust SDK

Rust primitives for implementing Stations, Satellites, and supporting services that speak PAP.

## Planned Features
- Protobuf-generated types using `prost`.
- Envelope signing and verification helpers leveraging `ring` or `ed25519-dalek`.
- Async gRPC client/server utilities built on `tonic`.
- Heartbeat scheduling utilities compatible with `tokio`.

## Getting Started
```
cargo build
```

Generated code will live under `src/gen` once protobuf build scripts are configured.
