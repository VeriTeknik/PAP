# PAP Protobuf Definitions

This directory hosts the canonical protocol buffer schemas for PAP v1. The initial focus is delivering the transport envelope and baseline message families used by the Station, Satellites, and Proxy.

## Layout
- `pap/v1/pap.proto`: Core transport schema.

## Tooling
1. Optional: Install `buf` and use the included config (`proto/buf.yaml`) to lint and format:
   ```bash
   make proto-lint
   make proto-format
   ```
2. Install the protobuf compiler (`protoc`) 3.21+.
3. Install language-specific plugins as SDKs come online (`protoc-gen-go`, `protoc-gen-ts`, etc.).
4. Generate code, for example:
   ```bash
   protoc --proto_path=. \
     --go_out=../sdk/go --go_opt=paths=source_relative \
     --python_out=../sdk/python \
     pap/v1/pap.proto
   ```
5. Ensure generated code is committed to language-specific subdirectories under `sdk/`.

## Contribution Guidelines
- Keep wire schemas backward compatible within `v1`.
- Use comments to document lifecycle invariants and validation expectations.
- When breaking changes are inevitable, introduce a new package version (e.g., `pap.v2`).
