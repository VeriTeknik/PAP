# PAP SDK Conformance Tests

This suite will exercise protocol compatibility across all SDKs. Each test will leverage fixtures generated from `proto/pap/v1/pap.proto` and validate envelope signing, invoke lifecycles, and heartbeat semantics.

## Planned Suites
- **handshake**: Validates version negotiation, capability exchange, and acknowledgement flow.
- **invoke**: Ensures request/response sequencing and deadline propagation.
- **event**: Confirms heartbeat payload requirements and telemetry routing.
- **control**: Verifies Station-issued lifecycle directives and Satellite acknowledgements.

## Execution Targets
- Node (TypeScript)
- Python 3.10+
- Rust (cargo test)
- Go 1.21+

Test harness code will live alongside language bindings once protobuf generation is integrated.
