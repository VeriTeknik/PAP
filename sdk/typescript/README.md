# PAP TypeScript SDK

This package will provide a Node/browser-ready client for orchestrating Satellites, signing envelopes, and streaming telemetry over PAP.

## Roadmap
- Generate TypeScript types from `proto/pap/v1/pap.proto` using `buf` or `ts-proto`.
- Wrap gRPC-web and Node transports with shared retry and deadline helpers.
- Offer heartbeat schedulers and lifecycle directive handlers.
- Publish the package to npm under `@pluggedin/pap-sdk`.

## Development
```
npm install
npm run build
```

Generated files will live under `src/gen` once protobuf generation is wired in.
