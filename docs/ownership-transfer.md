# PAP Ownership Transfer Protocol

**Version**: 1.0
**Status**: Draft
**Last Updated**: November 4, 2025

## 1. Overview

The Ownership Transfer Protocol enables safe migration of agents between Stations while preserving identity, state, and operational continuity. This is critical for multi-region deployments, disaster recovery, and organizational changes.

### 1.1 Use Cases

- **Multi-region migration**: Move agent to closer datacenter
- **Load balancing**: Redistribute agents across Stations
- **Disaster recovery**: Failover to backup Station
- **Organizational change**: Transfer ownership to new team/company
- **Maintenance**: Temporarily move agents during Station upgrade

### 1.2 Design Goals

- **Zero downtime**: Agent remains operational during transfer
- **State preservation**: Complete memory and context transfer
- **Security**: Credential rotation and encrypted state transfer
- **Auditability**: Complete trail of ownership chain
- **Atomicity**: Transfer either completes fully or rolls back

---

## 2. Transfer Sequence

### 2.1 Full Transfer Flow

```
┌────────────┐                ┌────────────┐                ┌────────────┐
│  Station A │                │    Agent   │                │  Station B │
│   (Old)    │                │            │                │   (New)    │
└─────┬──────┘                └──────┬─────┘                └──────┬─────┘
      │                              │                             │
      │  1. TransferInit             │                             │
      │────────────────────────────> │                             │
      │                              │                             │
      │                              │  2. TransferRequest          │
      │                              │──────────────────────────>  │
      │                              │                             │
      │                              │  3. TransferAccept           │
      │                              │  (new credentials)           │
      │                              │<────────────────────────────│
      │                              │                             │
      │                              │  4. Dual Connection          │
      │                              ├─────────────────────────────│
      │─────────────────────────────┤                             │
      │                              │                             │
      │  5. State Snapshot Transfer  │                             │
      │────────────────────────────>─────────────────────────────>│
      │         (encrypted)          │                             │
      │                              │                             │
      │  6. Revoke Old Credentials   │                             │
      │────────────────────────────> │                             │
      │                              │                             │
      │                              │  7. TransferComplete         │
      │<─────────────────────────────────────────────────────────│
      │                              │                             │
      │  8. Acknowledge              │                             │
      │────────────────────────────>─────────────────────────────>│
      │                              │                             │
      │  (Old connection closed)     │  (New Station active)       │
      │                              │                             │
```

### 2.2 Step-by-Step Protocol

**Step 1: Transfer Initiation**
```protobuf
message TransferInit {
  string agent_uuid = 1;            // "namespace/agent@v1.2"
  string target_station = 2;        // "station-b.example.com"
  bool preserve_state = 3;          // Transfer memory/state
  google.protobuf.Timestamp initiated_at = 4;
}
```

Old Station sends TransferInit to Agent with target Station details.

**Step 2: Transfer Request**
Agent contacts New Station with transfer token from Old Station.

**Step 3: Transfer Accept**
```protobuf
message TransferAccept {
  string agent_uuid = 1;
  Credentials new_credentials = 2;  // TLS cert, signing keys
  string transfer_token = 3;        // Time-bound authorization
  google.protobuf.Timestamp expires_at = 4;
}
```

New Station issues temporary credentials (valid for transfer duration only).

**Step 4: Dual Connection**
Agent maintains connections to both Stations during transfer.

**Step 5: State Snapshot Transfer**
Old Station transfers encrypted state snapshot to New Station via Agent.

**Step 6: Credential Revocation**
Old Station revokes agent's old credentials.

**Step 7: Transfer Complete**
```protobuf
message TransferComplete {
  string agent_uuid = 1;
  string old_station = 2;           // "plugged.in"
  string new_station = 3;           // "station-b.example.com"
  bool keys_rotated = 4;            // Confirmation
  google.protobuf.Timestamp completed_at = 5;
}
```

**Step 8: Acknowledgment**
Both Stations log transfer completion for audit trail.

---

## 3. State Transfer

### 3.1 State Snapshot Format

```json
{
  "version": "1.0",
  "agent_uuid": "namespace/research@v1.2",
  "captured_at": "2025-11-04T12:34:56Z",
  "state": {
    "memory": {
      "type": "vector",
      "vectors": [...],
      "metadata": {...}
    },
    "context": {
      "active_tasks": [...],
      "conversation_history": [...],
      "tool_state": {...}
    },
    "configuration": {
      "mcp_servers": [...],
      "models": [...],
      "policies": {...}
    }
  },
  "checksum": "sha256:abcd...",
  "encryption": {
    "algorithm": "AES-256-GCM",
    "key_exchange": "ECDH-P256"
  }
}
```

### 3.2 Encryption

**Key Exchange**:
1. New Station generates ephemeral ECDH key pair
2. Agent generates ephemeral ECDH key pair
3. Shared secret derived via ECDH
4. AES-256-GCM key derived from shared secret

**State Encryption**:
```
encrypted_state = AES-256-GCM(
  key = ECDH(station_ephemeral_private, agent_ephemeral_public),
  plaintext = state_snapshot,
  associated_data = "agent_uuid|old_station|new_station"
)
```

### 3.3 Chunked Transfer

Large states (>10 MB) are transferred in chunks:

```json
{
  "chunk_id": 1,
  "total_chunks": 10,
  "data": "base64-encoded-chunk",
  "checksum": "sha256:..."
}
```

---

## 4. Credential Rotation

### 4.1 Certificate Rotation

**Old Credentials** (revoked after transfer):
- TLS client certificate issued by Old Station CA
- Ed25519 signing key managed by Old Station
- DNS entry under Old Station's zone

**New Credentials** (issued during transfer):
- TLS client certificate issued by New Station CA
- New Ed25519 signing key managed by New Station
- DNS entry under New Station's zone (or kept same via delegation)

### 4.2 Rotation Timeline

```
T0: TransferInit
  - Old credentials valid
  - Agent operational on Old Station

T0+30s: TransferAccept
  - New credentials issued (temporary)
  - Both credentials valid (dual connection)
  - Agent operational on both Stations

T0+60s: State Transfer Complete
  - New credentials activated (permanent)
  - Old credentials revoked
  - Agent operational on New Station only

T0+90s: Transfer Complete
  - Old Station releases agent
  - New Station assumes full control
```

---

## 5. Failure Modes and Recovery

### 5.1 Transfer Timeout

**Condition**: Transfer not completed within time limit (default: 5 minutes)

**Recovery**:
1. New Station rejects transfer
2. Old Station retains control
3. Agent continues on Old Station
4. Transfer can be retried

### 5.2 Network Partition

**Condition**: Agent loses connection to one or both Stations

**Recovery**:
- **Old Station unreachable**: Agent continues with New Station
- **New Station unreachable**: Agent rolls back to Old Station
- **Both unreachable**: Agent enters DRAINING state, completes tasks, shuts down

### 5.3 State Corruption

**Condition**: State snapshot fails validation

**Recovery**:
1. New Station requests re-transfer
2. If second attempt fails, transfer aborted
3. Agent remains on Old Station
4. Alert sent to operations

### 5.4 Partial Transfer

**Condition**: Transfer interrupted mid-stream

**Recovery**:
1. Agent remains connected to Old Station
2. Partial state on New Station discarded
3. Transfer retried from beginning
4. Maximum 3 retry attempts

---

## 6. Security Considerations

### 6.1 Authorization

- Transfer MUST be signed by Old Station's authority key
- New Station MUST validate transfer token
- Agent MUST verify both Station identities (certificate chains)

### 6.2 State Encryption

- State MUST be encrypted in transit and at rest
- Encryption keys MUST be ephemeral (destroyed after transfer)
- State MUST include HMAC for integrity verification

### 6.3 Audit Trail

All transfer events MUST be logged:

```json
{
  "event": "transfer_init",
  "timestamp": "2025-11-04T12:34:56Z",
  "agent_uuid": "namespace/research@v1.2",
  "old_station": "plugged.in",
  "new_station": "station-b.example.com",
  "initiated_by": "admin@plugged.in",
  "transfer_token": "token-xyz"
}
```

### 6.4 Rollback Protection

- Transferred agents CANNOT be transferred back within 24 hours
- Prevents transfer loops and ownership disputes
- Override requires Station authority signature

---

## 7. DNS Management

### 7.1 DNS Update During Transfer

**Option 1: DNS Delegation (Preferred)**
```
; Before transfer
research.us-east.a.plugged.in.  IN  CNAME  research.stationA.internal.

; After transfer
research.us-east.a.plugged.in.  IN  CNAME  research.stationB.internal.
```

**Option 2: Keep DNS, Update Backend**
DNS entry remains same, backend routing updated via Service Registry.

### 7.2 TTL Management

- Reduce TTL to 60s before transfer (for faster propagation)
- Update DNS record during transfer
- Restore normal TTL (300s) after transfer complete

---

## 8. API Reference

### 8.1 Initiate Transfer

**Endpoint**: `POST /api/v1/agents/{agentId}/transfer/init`

**Request**:
```json
{
  "target_station": "station-b.example.com",
  "preserve_state": true,
  "timeout_seconds": 300
}
```

**Response**:
```json
{
  "transfer_id": "xfer-abc123",
  "status": "initiated",
  "expires_at": "2025-11-04T12:39:56Z"
}
```

### 8.2 Accept Transfer

**Endpoint**: `POST /api/v1/transfers/{transferId}/accept`

**Request**:
```json
{
  "agent_uuid": "namespace/research@v1.2",
  "credentials": {
    "tls_cert": "-----BEGIN CERTIFICATE-----\n...",
    "signing_key_ref": "vault://keys/agent-new"
  }
}
```

**Response**:
```json
{
  "status": "accepted",
  "transfer_token": "token-xyz",
  "expires_at": "2025-11-04T12:39:56Z"
}
```

### 8.3 Complete Transfer

**Endpoint**: `POST /api/v1/transfers/{transferId}/complete`

**Request**:
```json
{
  "agent_uuid": "namespace/research@v1.2",
  "state_checksum": "sha256:abcd...",
  "keys_rotated": true
}
```

**Response**:
```json
{
  "status": "completed",
  "completed_at": "2025-11-04T12:36:56Z"
}
```

---

## 9. Implementation Checklist

### Old Station
- [ ] Transfer initiation API
- [ ] State snapshot generation
- [ ] State encryption (AES-256-GCM)
- [ ] Credential revocation
- [ ] Audit logging
- [ ] Timeout handling

### New Station
- [ ] Transfer acceptance API
- [ ] New credential issuance
- [ ] State decryption and validation
- [ ] Service registry update
- [ ] DNS update (if applicable)
- [ ] Audit logging

### Agent
- [ ] Dual connection support
- [ ] State serialization
- [ ] Credential rotation
- [ ] Rollback handling
- [ ] Transfer status reporting

---

## 10. Testing Scenarios

### 10.1 Happy Path
1. Initiate transfer with preserved state
2. Accept transfer on new Station
3. Transfer state successfully
4. Rotate credentials
5. Complete transfer
6. Verify agent operational on new Station

### 10.2 Timeout Recovery
1. Initiate transfer
2. Simulate network delay
3. Transfer times out
4. Verify agent remains on old Station
5. Retry transfer successfully

### 10.3 Network Partition
1. Initiate transfer
2. Disconnect agent from old Station mid-transfer
3. Agent continues to new Station
4. Verify state integrity

### 10.4 State Corruption
1. Initiate transfer
2. Corrupt state snapshot in transit
3. New Station detects corruption
4. Transfer aborted
5. Agent remains on old Station

---

**Document Version**: 1.0
**Status**: Draft
**Last Updated**: November 4, 2025
