# PAP Go SDK

Go helpers for implementing PAP-aware services and agents.

## Planned Capabilities
- gRPC client/server wrappers built on `grpc-go`.
- Envelope signing/verification helpers using `crypto/ed25519`.
- Heartbeat emission utilities and lifecycle directive handlers.
- Conformance test harness shared with other SDKs.

## Usage
```
go mod tidy
go test ./...
```

Generated protobuf types will live under `papv1` once build tooling is configured.
