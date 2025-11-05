# PAP-Hooks Specification v1.0

**Status**: Draft
**Profile**: PAP-Hooks (Open I/O)
**Audience**: External integrators, MCP server developers, tool builders

## 1. Overview

PAP-Hooks is the open, vendor-neutral I/O profile of the Plugged.in Agent Protocol. It enables agents to interact with external services, MCP servers, A2A peers, and third-party APIs using industry-standard protocols.

### 1.1 Profile Comparison

| Aspect | PAP-CP (Control Plane) | PAP-Hooks (Open I/O) |
|--------|----------------------|---------------------|
| **Transport** | gRPC/HTTP/2 + TLS 1.3 | JSON-RPC 2.0 over WebSocket/SSE |
| **Authentication** | Mutual TLS (mTLS) | OAuth 2.1 + JWT |
| **Wire Format** | Protocol Buffers v3 | UTF-8 JSON |
| **Security** | Ed25519 signatures | JOSE/JWT signing |
| **Use Cases** | Lifecycle management, critical control | Tool invocation, external APIs, webhooks |
| **Replay Protection** | Nonce cache (≥60s) | JWT exp/iat claims |

### 1.2 Design Goals

- **MCP Compatibility**: Native support for Model Context Protocol servers
- **A2A Integration**: Seamless agent-to-agent delegation
- **Vendor Neutrality**: No lock-in to proprietary protocols
- **Browser Support**: WebSocket and SSE for web-based agents
- **OAuth 2.1 Standard**: Industry-standard authorization

## 2. Transport Bindings

### 2.1 WebSocket (Preferred)

**Endpoint Format**: `wss://{agent}.{region}.a.plugged.in/hooks`

**Connection Establishment**:
```javascript
const ws = new WebSocket('wss://research.us-east.a.plugged.in/hooks', {
  headers: {
    'Authorization': 'Bearer {jwt-token}',
    'Sec-WebSocket-Protocol': 'pap-hooks-v1'
  }
});
```

**Message Format**:
```json
{
  "jsonrpc": "2.0",
  "id": "req-12345",
  "method": "tool.invoke",
  "params": {
    "tool": "web-search",
    "arguments": {"query": "quantum computing"},
    "context": {
      "agent_uuid": "namespace/research@v1.2",
      "trace_id": "trace-xyz",
      "authorization": "Bearer {jwt-token}"
    }
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": "req-12345",
  "result": {
    "status": "success",
    "data": {
      "results": [
        {"title": "Quantum Computing Basics", "url": "https://..."}
      ]
    },
    "metadata": {
      "duration_ms": 120,
      "cost": 0.001
    }
  }
}
```

### 2.2 Server-Sent Events (SSE)

**Use Case**: Browser-based agents without WebSocket support

**Endpoint**: `https://{agent}.{region}.a.plugged.in/hooks/stream`

**Request**:
```http
GET /hooks/stream HTTP/1.1
Host: research.us-east.a.plugged.in
Authorization: Bearer {jwt-token}
Accept: text/event-stream
Cache-Control: no-cache
```

**Response Stream**:
```
event: tool.result
id: msg-001
data: {"tool":"web-search","status":"success","result":{...}}

event: heartbeat
id: msg-002
data: {"timestamp":1699000000}

event: tool.result
id: msg-003
data: {"tool":"filesystem","status":"success","result":{...}}
```

### 2.3 HTTP Streaming (Alternative)

**Endpoint**: `https://{agent}.{region}.a.plugged.in/hooks/invoke`

**Request**:
```http
POST /hooks/invoke HTTP/1.1
Host: research.us-east.a.plugged.in
Authorization: Bearer {jwt-token}
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "req-12345",
  "method": "tool.invoke",
  "params": {...}
}
```

## 3. Authentication and Authorization

### 3.1 OAuth 2.1 Flow

**Grant Types Supported**:
- **Authorization Code with PKCE** (public clients, web apps)
- **Client Credentials** (server-to-server, backend agents)

**Token Endpoint**: `https://auth.plugged.in/token`

**Authorization Request**:
```http
POST /token HTTP/1.1
Host: auth.plugged.in
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=agent-abc123
&client_secret={secret}
&scope=tool.invoke a2a.delegate
```

**Token Response**:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "tool.invoke a2a.delegate",
  "refresh_token": "refresh-xyz..."
}
```

### 3.2 JWT Claims

**Required Claims**:
```json
{
  "iss": "https://auth.plugged.in",
  "sub": "agent-abc123",
  "aud": "https://hooks.plugged.in",
  "exp": 1699000000,
  "iat": 1698996400,
  "agent_uuid": "namespace/research@v1.2",
  "station_id": "plugged.in",
  "scopes": ["tool.invoke", "a2a.delegate"],
  "capabilities": ["mcp-2025-06-18", "a2a-0.3"]
}
```

### 3.3 Token Refresh

**Refresh Request**:
```http
POST /token HTTP/1.1
Host: auth.plugged.in
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token={refresh-token}
&client_id=agent-abc123
```

## 4. Message Protocols

### 4.1 JSON-RPC 2.0 Methods

**Tool Invocation**:
```json
{
  "jsonrpc": "2.0",
  "method": "tool.invoke",
  "params": {
    "tool": "filesystem",
    "operation": "read",
    "arguments": {"path": "/data/config.json"}
  },
  "id": "req-001"
}
```

**A2A Delegation**:
```json
{
  "jsonrpc": "2.0",
  "method": "a2a.delegate",
  "params": {
    "target_agent": "namespace/worker@v1.0",
    "task": {
      "type": "analyze",
      "data": {"document_id": "doc-123"}
    }
  },
  "id": "req-002"
}
```

**MCP Server Access**:
```json
{
  "jsonrpc": "2.0",
  "method": "mcp.resource.read",
  "params": {
    "server": "web-search@v1.5",
    "uri": "search://quantum-computing"
  },
  "id": "req-003"
}
```

### 4.2 Error Responses

**Standard Error Format**:
```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "pap_code": "DEPENDENCY_FAILED",
      "details": "MCP server timeout",
      "retry_after": 5
    }
  }
}
```

**PAP Error Code Mapping**:

| PAP Code | JSON-RPC Code | Description |
|----------|--------------|-------------|
| BAD_REQUEST | -32602 | Invalid params |
| UNAUTHORIZED | -32001 | Authentication failed |
| NOT_FOUND | -32601 | Method not found |
| TIMEOUT | -32000 | Request timeout |
| RATE_LIMITED | -32004 | Too many requests |
| DEPENDENCY_FAILED | -32603 | Internal error |
| INTERNAL_ERROR | -32603 | Internal error |

## 5. Hook Specifications

### 5.1 Hook Definition Format

```json
{
  "hookId": "http-api@v1",
  "transport": "pap_hooks",
  "endpoint": {
    "baseUrl": "https://api.external.com",
    "authentication": {
      "type": "oauth2",
      "clientIdRef": "vault://secrets/external/client-id",
      "clientSecretRef": "vault://secrets/external/secret",
      "tokenEndpoint": "https://api.external.com/oauth/token",
      "scopes": ["read", "write"]
    }
  },
  "operations": [
    {
      "operationId": "search",
      "method": "POST",
      "path": "/v1/search",
      "requestSchema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "limit": {"type": "integer"}
        },
        "required": ["query"]
      },
      "responseSchema": {
        "type": "object",
        "properties": {
          "results": {"type": "array"}
        }
      },
      "rateLimits": {
        "requestsPerMinute": 60,
        "burstSize": 10
      }
    }
  ],
  "security": {
    "allowedDomains": ["api.external.com"],
    "validateCertificates": true,
    "requireSignature": false
  }
}
```

### 5.2 MCP Server Hook

```json
{
  "hookId": "mcp-filesystem@v2.1",
  "transport": "pap_hooks",
  "protocol": "mcp",
  "endpoint": {
    "baseUrl": "wss://mcp.plugged.in/servers/filesystem"
  },
  "capabilities": [
    {
      "type": "resource",
      "patterns": ["file://**"]
    },
    {
      "type": "tool",
      "names": ["read_file", "write_file", "list_directory"]
    }
  ]
}
```

### 5.3 A2A Peer Hook

```json
{
  "hookId": "a2a-worker@v1.0",
  "transport": "pap_hooks",
  "protocol": "a2a",
  "endpoint": {
    "baseUrl": "https://worker.us-east.a.plugged.in/a2a/"
  },
  "agentCard": {
    "name": "Worker Agent",
    "description": "Data processing worker",
    "capabilities": ["analyze", "transform", "aggregate"],
    "version": "1.0.0"
  }
}
```

## 6. Security Considerations

### 6.1 Transport Security

- **TLS 1.3 REQUIRED**: All connections MUST use TLS 1.3
- **Certificate Validation**: Agents MUST validate server certificates
- **Hostname Verification**: Agents MUST verify certificate SANs match endpoint

### 6.2 Token Security

- **Token Lifetime**: Access tokens SHOULD have ≤1 hour lifetime
- **Refresh Rotation**: Refresh tokens MUST rotate on use
- **Scope Minimization**: Tokens SHOULD have minimal required scopes
- **Secure Storage**: Tokens MUST be stored securely (not in logs/git)

### 6.3 Rate Limiting

**Gateway Enforcement**:
```json
{
  "rateLimits": {
    "requestsPerMinute": 60,
    "requestsPerHour": 1000,
    "burstSize": 10,
    "concurrent": 5
  }
}
```

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699000000
```

### 6.4 Input Validation

- **Schema Validation**: All requests MUST validate against declared schemas
- **Size Limits**: Request bodies SHOULD be ≤10 MB
- **Timeout Enforcement**: Requests MUST timeout after configured duration
- **Circuit Breakers**: Gateways SHOULD implement circuit breakers for failing hooks

## 7. Observability

### 7.1 Trace Propagation

**Request Headers**:
```http
Traceparent: 00-{trace-id}-{span-id}-01
Tracestate: pap=agent-abc123
```

**JSON-RPC Context**:
```json
{
  "jsonrpc": "2.0",
  "method": "tool.invoke",
  "params": {
    "tool": "web-search",
    "arguments": {...},
    "context": {
      "trace_id": "trace-xyz",
      "span_id": "span-123",
      "parent_span_id": "span-000"
    }
  },
  "id": "req-001"
}
```

### 7.2 Metrics

**Client Metrics**:
- `pap_hooks_requests_total{method, status}` - Request counter
- `pap_hooks_request_duration_seconds{method}` - Request latency histogram
- `pap_hooks_errors_total{error_code}` - Error counter

**Gateway Metrics**:
- `pap_hooks_gateway_requests_total{agent, hook}` - Gateway requests
- `pap_hooks_gateway_rate_limit_hits_total{agent}` - Rate limit violations
- `pap_hooks_gateway_circuit_breaker_state{hook}` - Circuit breaker status

## 8. Protocol Interoperability

### 8.1 MCP Compatibility

PAP-Hooks is designed for seamless MCP integration:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "web-search",
    "arguments": {"query": "quantum computing"}
  },
  "id": "mcp-001"
}
```

Gateway translates to PAP-Hooks format automatically.

### 8.2 A2A Compatibility

A2A task delegation maps directly to PAP-Hooks:

```json
{
  "jsonrpc": "2.0",
  "method": "a2a.delegate",
  "params": {
    "taskCard": {
      "type": "analyze",
      "input": {"document_id": "doc-123"}
    }
  },
  "id": "a2a-001"
}
```

### 8.3 Gateway Translation

Gateways **MAY** translate between PAP-CP and PAP-Hooks:

```
Agent --[PAP-CP/gRPC]--> Gateway --[PAP-Hooks/JSON-RPC]--> External API
```

Translation preserves semantics, error codes, and trace context.

## 9. Implementation Guidelines

### 9.1 Client SDK Requirements

All PAP-Hooks client SDKs MUST provide:

- OAuth 2.1 token management (acquisition, refresh, rotation)
- WebSocket and SSE transport support
- JSON-RPC 2.0 message encoding/decoding
- Automatic retry with exponential backoff
- Circuit breaker implementation
- Trace context propagation
- Error mapping to PAP error codes

### 9.2 Gateway Implementation

Gateways MUST implement:

- Token validation and scope enforcement
- Rate limiting per agent and hook
- Circuit breakers for failing hooks
- Request/response logging with trace IDs
- Metrics emission (Prometheus format)
- Hook configuration loading

### 9.3 Conformance Testing

Implementations MUST pass:

- OAuth 2.1 compliance tests
- JSON-RPC 2.0 protocol tests
- WebSocket/SSE transport tests
- Error handling tests
- Rate limiting tests
- Trace propagation tests

## 10. Future Extensions

**Planned Features**:
- GraphQL support for hooks
- Binary protocol options (MessagePack, CBOR)
- Advanced retry policies (jitter, backoff strategies)
- Hook versioning and migration
- Multi-region hook routing

## 11. References

- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [OAuth 2.1 Draft](https://oauth.net/2.1/)
- [RFC 8693: OAuth 2.0 Token Exchange](https://datatracker.ietf.org/doc/html/rfc8693)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Agent-to-Agent Protocol](https://a2a-protocol.org/)
- [OpenTelemetry Trace Context](https://www.w3.org/TR/trace-context/)

---

**Document Version**: 1.0
**Status**: Draft
**Last Updated**: November 4, 2025
**Protocol Version**: PAP-Hooks v1.0
