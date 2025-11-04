# PAP Service Registry

**Version**: 1.0
**Status**: Draft
**Last Updated**: November 4, 2025

## 1. Overview

The PAP Service Registry provides DNS-based agent service discovery and capability advertisement. It extends the Model Context Protocol's registry pattern to support agent lifecycle management, multi-protocol operation, and distributed routing.

### 1.1 Design Principles

- **DNS-Native**: Leverage existing DNS infrastructure for discovery
- **MCP-Compatible**: Extend MCP registry schema with agent-specific fields
- **Multi-Protocol**: Support PAP-CP, PAP-Hooks, MCP, and A2A endpoints
- **Distributed**: Enable cross-region and cross-Station discovery

---

## 2. Agent Service Schema

### 2.1 Core Schema

```json
{
  "$schema": "https://plugged.in/schemas/2025-11/agent.schema.json",
  "agentId": "namespace/research@v1.2",
  "endpoint": {
    "url": "https://research.us-east.a.plugged.in/agent/",
    "region": "us-east",
    "protocols": {
      "pap_cp": "grpc://research.internal:50051",
      "pap_hooks": "wss://research.us-east.a.plugged.in/hooks/",
      "a2a": "https://research.us-east.a.plugged.in/a2a/"
    }
  },
  "capabilities": {
    "supportedProtocols": {
      "pap": "1.0",
      "a2a": "0.3.0",
      "mcp": "2025-06-18"
    },
    "mcpServers": ["filesystem@2.1", "web-search@1.5"],
    "orchestrationPatterns": ["supervisor", "peer", "worker"],
    "models": ["gpt-4", "claude-3-opus"]
  },
  "lifecycle": {
    "state": "ACTIVE",
    "version": "1.2.0",
    "created": "2025-11-01T00:00:00Z",
    "lastHeartbeat": "2025-11-04T12:34:56Z",
    "uptime": 259200
  },
  "metadata": {
    "name": "Research Agent",
    "description": "Autonomous research and analysis agent",
    "tags": ["research", "analysis", "web-search"],
    "owner": "org-abc123"
  },
  "_meta": {
    "io.plugged.registry/provisioner": {
      "owner": "org-abc123",
      "station": "plugged.in"
    }
  }
}
```

### 2.2 Schema Fields

#### agentId (required)
Format: `namespace/agent@version`
- **namespace**: Organization or project identifier
- **agent**: Agent name (lowercase, alphanumeric + hyphens)
- **version**: Semantic version (major.minor.patch)

Examples:
- `pluggedin/research@1.2.0`
- `acme-corp/data-processor@2.0.1`
- `personal/focus@0.1.0`

#### endpoint (required)
Primary agent endpoint with protocol-specific URIs.

**Fields**:
- `url`: Primary HTTP(S) endpoint
- `region`: Deployment region (us-east, eu-west, ap-south, etc.)
- `protocols`: Protocol-specific endpoints

**Protocol Endpoints**:
```json
{
  "pap_cp": "grpc://agent.internal:50051",      // Internal control plane
  "pap_hooks": "wss://agent.region.a.plugged.in/hooks/",  // Public hooks
  "a2a": "https://agent.region.a.plugged.in/a2a/",        // A2A delegation
  "mcp": "wss://agent.region.a.plugged.in/mcp/"           // MCP compatibility
}
```

#### capabilities (required)
Agent capabilities and protocol support.

**supportedProtocols**: Protocol versions
```json
{
  "pap": "1.0",           // PAP version
  "a2a": "0.3.0",         // A2A version
  "mcp": "2025-06-18"     // MCP version
}
```

**mcpServers**: Configured MCP servers
```json
[
  "filesystem@2.1",
  "web-search@1.5",
  "brave-search@1.0",
  "github@1.2"
]
```

**orchestrationPatterns**: Agent roles
- `supervisor`: Coordinates other agents
- `peer`: Collaborates with equals
- `worker`: Executes delegated tasks
- `standalone`: Operates independently

**models**: Available LLM models
```json
[
  "gpt-4",
  "gpt-4-turbo",
  "claude-3-opus",
  "claude-3-sonnet"
]
```

#### lifecycle (required)
Current lifecycle state and version.

**state**: One of: NEW, PROVISIONED, ACTIVE, DRAINING, TERMINATED, KILLED

**version**: Current agent version (semantic versioning)

**created**: ISO 8601 timestamp of agent creation

**lastHeartbeat**: ISO 8601 timestamp of last heartbeat

**uptime**: Seconds since agent started

#### metadata (optional)
Human-readable metadata and tags.

**name**: Display name

**description**: Agent purpose and capabilities

**tags**: Searchable tags for discovery

**owner**: Organization or user identifier

---

## 3. DNS-Based Discovery

### 3.1 DNS Records

Agents are discoverable via DNS:

```
; Agent A record
research.us-east.a.plugged.in.  IN  A  10.0.1.50

; Service discovery via TXT record
research.us-east.a.plugged.in.  IN  TXT  "pap-version=1.0"
research.us-east.a.plugged.in.  IN  TXT  "agent-id=namespace/research@1.2"

; Protocol endpoints via SRV records
_pap-cp._tcp.research.us-east.a.plugged.in.  IN  SRV  10 10 50051 research.internal.
_pap-hooks._tcp.research.us-east.a.plugged.in.  IN  SRV  10 10 443 research.us-east.a.plugged.in.
```

### 3.2 DNS Query Examples

**Discover agent endpoint**:
```bash
dig research.us-east.a.plugged.in A
# Returns: 10.0.1.50

dig research.us-east.a.plugged.in TXT
# Returns: "pap-version=1.0" "agent-id=namespace/research@1.2"
```

**Discover PAP-CP endpoint**:
```bash
dig _pap-cp._tcp.research.us-east.a.plugged.in SRV
# Returns: 10 10 50051 research.internal.
```

### 3.3 DNSSEC Requirements

- All agent subzones MUST be DNSSEC-signed
- Resolvers MUST validate DNSSEC signatures
- Invalid signatures MUST result in discovery failure

---

## 4. Registry API

### 4.1 Agent Registration

**Endpoint**: `POST /registry/v1/agents`

**Request**:
```json
{
  "agentId": "namespace/research@1.2",
  "endpoint": {
    "url": "https://research.us-east.a.plugged.in/agent/",
    "region": "us-east"
  },
  "capabilities": {
    "supportedProtocols": {
      "pap": "1.0",
      "mcp": "2025-06-18"
    }
  }
}
```

**Response**:
```json
{
  "status": "success",
  "agentId": "namespace/research@1.2",
  "registeredAt": "2025-11-04T12:34:56Z",
  "dns": {
    "fqdn": "research.us-east.a.plugged.in",
    "ttl": 300
  }
}
```

### 4.2 Agent Discovery

**Endpoint**: `GET /registry/v1/agents/{agentId}`

**Response**:
```json
{
  "agentId": "namespace/research@1.2",
  "endpoint": {
    "url": "https://research.us-east.a.plugged.in/agent/",
    "region": "us-east",
    "protocols": {
      "pap_cp": "grpc://research.internal:50051",
      "pap_hooks": "wss://research.us-east.a.plugged.in/hooks/"
    }
  },
  "lifecycle": {
    "state": "ACTIVE",
    "lastHeartbeat": "2025-11-04T12:34:56Z"
  }
}
```

### 4.3 Agent Search

**Endpoint**: `GET /registry/v1/agents?tags=research&region=us-east`

**Response**:
```json
{
  "agents": [
    {
      "agentId": "namespace/research@1.2",
      "endpoint": {...},
      "capabilities": {...},
      "metadata": {
        "tags": ["research", "analysis"]
      }
    }
  ],
  "total": 1,
  "page": 1
}
```

### 4.4 Agent Update

**Endpoint**: `PATCH /registry/v1/agents/{agentId}`

**Request**:
```json
{
  "lifecycle": {
    "state": "DRAINING"
  },
  "metadata": {
    "tags": ["research", "analysis", "archived"]
  }
}
```

### 4.5 Agent Deregistration

**Endpoint**: `DELETE /registry/v1/agents/{agentId}`

**Response**:
```json
{
  "status": "success",
  "agentId": "namespace/research@1.2",
  "deregisteredAt": "2025-11-04T12:34:56Z"
}
```

---

## 5. Capability Negotiation

### 5.1 Protocol Version Negotiation

Agents and clients negotiate protocol versions during handshake:

**Client Request**:
```json
{
  "supportedProtocols": {
    "pap": ["1.0", "0.9"],
    "mcp": ["2025-06-18", "2024-11-05"]
  }
}
```

**Agent Response**:
```json
{
  "selectedProtocols": {
    "pap": "1.0",
    "mcp": "2025-06-18"
  }
}
```

### 5.2 Capability Matching

Stations match agents to tasks based on capabilities:

```json
{
  "taskRequirements": {
    "orchestrationPattern": "worker",
    "mcpServers": ["web-search"],
    "minVersion": "1.0"
  },
  "matchedAgents": [
    {
      "agentId": "namespace/research@1.2",
      "score": 0.95,
      "endpoint": "https://research.us-east.a.plugged.in/agent/"
    }
  ]
}
```

---

## 6. MCP Compatibility

### 6.1 MCP Registry Mapping

PAP Service Registry extends MCP's registry pattern:

| MCP Field | PAP Equivalent |
|-----------|----------------|
| `name` | `agentId` |
| `version` | `capabilities.supportedProtocols.mcp` |
| `resources` | `capabilities.mcpServers` (resource providers) |
| `tools` | Exposed via MCP servers |
| `prompts` | Exposed via MCP servers |

### 6.2 MCP Server Discovery

Agents advertise MCP server access:

```json
{
  "agentId": "namespace/research@1.2",
  "capabilities": {
    "mcpServers": [
      {
        "id": "web-search@1.5",
        "endpoint": "wss://research.us-east.a.plugged.in/mcp/web-search",
        "capabilities": {
          "resources": true,
          "tools": ["search", "summarize"],
          "prompts": false
        }
      }
    ]
  }
}
```

---

## 7. A2A Integration

### 7.1 Agent Card Generation

PAP agents automatically generate A2A Agent Cards:

```json
{
  "$schema": "https://a2a-protocol.org/schemas/agent-card.json",
  "name": "Research Agent",
  "description": "Autonomous research and analysis agent",
  "version": "1.2.0",
  "endpoint": "https://research.us-east.a.plugged.in/a2a/",
  "capabilities": {
    "orchestrationPatterns": ["peer", "worker"],
    "supportedOperations": ["analyze", "research", "summarize"]
  },
  "authentication": {
    "type": "oauth2",
    "tokenEndpoint": "https://auth.plugged.in/token"
  }
}
```

### 7.2 A2A Discovery

Agents discover peers via Service Registry:

```json
{
  "query": {
    "orchestrationPattern": "peer",
    "capabilities": ["analyze"]
  },
  "results": [
    {
      "agentId": "namespace/analyzer@2.0",
      "a2aEndpoint": "https://analyzer.us-east.a.plugged.in/a2a/",
      "agentCard": {...}
    }
  ]
}
```

---

## 8. Caching and TTLs

### 8.1 DNS TTLs

- Active agents: TTL 300s (5 minutes)
- Draining agents: TTL 60s (1 minute)
- Terminated agents: Immediate removal

### 8.2 Registry Cache

**Client Caching Strategy**:
```json
{
  "cache": {
    "ttl": 300,
    "maxAge": 600,
    "staleWhileRevalidate": 60
  }
}
```

**Cache Headers**:
```http
Cache-Control: max-age=300, stale-while-revalidate=60
ETag: "agent-research-v1.2-20251104"
```

---

## 9. Security Considerations

### 9.1 Registry Access Control

- Public discovery: Read-only, unauthenticated
- Agent registration: Station authentication required
- Agent updates: Agent mTLS certificate required
- Deregistration: Station authority required

### 9.2 DNS Security

- DNSSEC validation required
- DNS poisoning mitigation via DNSSEC
- Rate limiting on DNS queries (≤100 queries/minute per IP)

### 9.3 Endpoint Validation

- TLS certificate validation required
- Hostname verification against DNS records
- Certificate pinning recommended for high-security agents

---

## 10. Examples

### 10.1 Research Agent

```json
{
  "agentId": "pluggedin/research@1.2.0",
  "endpoint": {
    "url": "https://research.us-east.a.plugged.in/agent/",
    "region": "us-east",
    "protocols": {
      "pap_cp": "grpc://research.internal:50051",
      "pap_hooks": "wss://research.us-east.a.plugged.in/hooks/",
      "a2a": "https://research.us-east.a.plugged.in/a2a/"
    }
  },
  "capabilities": {
    "supportedProtocols": {
      "pap": "1.0",
      "a2a": "0.3.0",
      "mcp": "2025-06-18"
    },
    "mcpServers": [
      "web-search@1.5",
      "brave-search@1.0",
      "github@1.2"
    ],
    "orchestrationPatterns": ["supervisor", "peer"],
    "models": ["gpt-4", "claude-3-opus"]
  },
  "lifecycle": {
    "state": "ACTIVE",
    "version": "1.2.0",
    "created": "2025-11-01T00:00:00Z",
    "lastHeartbeat": "2025-11-04T12:34:56Z",
    "uptime": 259200
  },
  "metadata": {
    "name": "Research Agent",
    "description": "Autonomous research agent with web search and GitHub integration",
    "tags": ["research", "web-search", "github"],
    "owner": "pluggedin"
  }
}
```

### 10.2 Memory Agent

```json
{
  "agentId": "pluggedin/memory@2.0.0",
  "endpoint": {
    "url": "https://memory.us-east.a.plugged.in/agent/",
    "region": "us-east",
    "protocols": {
      "pap_cp": "grpc://memory.internal:50051",
      "pap_hooks": "wss://memory.us-east.a.plugged.in/hooks/"
    }
  },
  "capabilities": {
    "supportedProtocols": {
      "pap": "1.0",
      "mcp": "2025-06-18"
    },
    "mcpServers": [
      "vector-store@2.1",
      "graph-store@1.5"
    ],
    "orchestrationPatterns": ["worker"],
    "models": ["gpt-4"]
  },
  "lifecycle": {
    "state": "ACTIVE",
    "version": "2.0.0",
    "created": "2025-10-15T00:00:00Z",
    "lastHeartbeat": "2025-11-04T12:34:56Z",
    "uptime": 1728000
  },
  "metadata": {
    "name": "Memory Agent",
    "description": "Persistent memory and context management",
    "tags": ["memory", "vector-store", "graph"],
    "owner": "pluggedin"
  }
}
```

### 10.3 Worker Agent

```json
{
  "agentId": "acme/data-processor@1.0.0",
  "endpoint": {
    "url": "https://processor.us-east.a.plugged.in/agent/",
    "region": "us-east",
    "protocols": {
      "pap_cp": "grpc://processor.internal:50051",
      "pap_hooks": "wss://processor.us-east.a.plugged.in/hooks/",
      "a2a": "https://processor.us-east.a.plugged.in/a2a/"
    }
  },
  "capabilities": {
    "supportedProtocols": {
      "pap": "1.0",
      "a2a": "0.3.0"
    },
    "mcpServers": ["filesystem@2.1"],
    "orchestrationPatterns": ["worker"],
    "models": ["gpt-4-turbo"]
  },
  "lifecycle": {
    "state": "ACTIVE",
    "version": "1.0.0",
    "created": "2025-11-01T00:00:00Z",
    "lastHeartbeat": "2025-11-04T12:34:56Z",
    "uptime": 259200
  },
  "metadata": {
    "name": "Data Processor",
    "description": "High-throughput data processing worker",
    "tags": ["data-processing", "etl", "worker"],
    "owner": "acme-corp"
  }
}
```

---

## 11. Implementation Checklist

### Registry Service
- [ ] Agent registration endpoint
- [ ] Agent discovery API
- [ ] Agent search with filters
- [ ] DNS record management
- [ ] DNSSEC signing
- [ ] Cache management
- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] Audit logging

### Agent Client
- [ ] Auto-registration on provision
- [ ] Capability advertisement
- [ ] Heartbeat-triggered registry updates
- [ ] Graceful deregistration
- [ ] DNS lookup utilities
- [ ] Protocol version negotiation

### Gateway
- [ ] Registry cache with TTL
- [ ] DNS resolution with DNSSEC validation
- [ ] Endpoint routing based on registry
- [ ] Capability-based routing
- [ ] Circuit breaker per agent

---

**Document Version**: 1.0
**Status**: Draft
**Last Updated**: November 4, 2025
