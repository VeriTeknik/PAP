# PAP Evaluation Methodology

**Protocol Version**: PAP v1.0 (Paper-Aligned)
**Paper Version**: Draft v0.3 (for arXiv cs.DC)
**Document Type**: Benchmarking Guide
**Last Updated**: November 12, 2025

This document defines performance targets, evaluation criteria, and benchmarking procedures for PAP v1.0 implementations, as specified in the academic paper.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Performance Metrics](#2-performance-metrics)
- [3. Security Validation](#3-security-validation)
- [4. Interoperability Testing](#4-interoperability-testing)
- [5. Chaos Engineering](#5-chaos-engineering)
- [6. Benchmarking Procedures](#6-benchmarking-procedures)
- [7. References](#7-references)

---

## 1. Overview

### 1.1 Purpose

This evaluation methodology provides:
- **Concrete performance targets** for PAP implementations
- **Validation procedures** for security and reliability claims
- **Benchmarking guidelines** for comparative analysis
- **Chaos engineering scenarios** for resilience testing

### 1.2 Scope

Evaluations cover:
- Control plane operations (PAP-CP)
- Open I/O operations (PAP-Hooks)
- Gateway performance and translation
- End-to-end lifecycle scenarios
- Multi-agent coordination patterns

### 1.3 Test Environment

**Recommended Setup**:
- Kubernetes cluster: 3+ nodes, 16 vCPU, 64GB RAM each
- Network: 10 Gbps, <1ms intra-cluster latency
- Storage: SSD-backed persistent volumes
- Load generators: Locust, k6, or custom agents
- Observability: Prometheus, Grafana, Jaeger

---

## 2. Performance Metrics

### 2.1 E1: Control Plane Latency

**Target**: Sub-50ms P99 latency for control operations under load

#### Heartbeat Round-Trip
- **P50**: <5ms (median)
- **P90**: <10ms
- **P99**: <20ms (99th percentile)
- **Test conditions**: 1,000 concurrent agents, 30-second intervals
- **Measurement**: Agent send timestamp → Station acknowledgment receipt

**Procedure**:
```bash
# Start 1000 agents with heartbeat instrumentation
./load-test heartbeat --agents=1000 --duration=10m --interval=30s

# Measure with OpenTelemetry spans
# Export: otel.latency.heartbeat.p50, p90, p99
```

#### Control Message Processing
- **P50**: <10ms
- **P90**: <30ms
- **P99**: <50ms
- **Test conditions**: Mixed workload (invoke, terminate, query)
- **Measurement**: Gateway receive → Handler complete → Response sent

**Procedure**:
```bash
# Mixed control workload
./load-test control-mix --agents=1000 --duration=10m \
  --invoke-rate=100/s --terminate-rate=10/s --query-rate=50/s
```

#### Acceptance Criteria
- ✓ All P99 values under target across 3 consecutive 10-minute runs
- ✓ No degradation >10% under sustained load
- ✓ Recovery to baseline within 60 seconds after load spike

---

### 2.2 E2: Liveness Detection

**Target**: <0.1% false positive rate with rapid detection

#### False Positive Rate
- **Target**: <0.1% (1 in 1000 agents)
- **Definition**: Healthy agent incorrectly marked AGENT_UNHEALTHY (480)
- **Test conditions**: Network jitter (±5ms), 5% packet loss

**Procedure**:
```bash
# Run with network chaos injection
./load-test liveness --agents=1000 --duration=30m \
  --chaos-jitter=5ms --chaos-loss=5%

# Measure: false_positives / total_agents
```

#### Detection Latency
- **Target**: Within 1.5× configured heartbeat interval
- **IDLE mode (30s)**: Detection within 45 seconds
- **EMERGENCY mode (5s)**: Detection within 7.5 seconds

**Procedure**:
```bash
# Kill agent processes and measure detection time
./load-test zombie-detection --agents=100 --kill-random=10 \
  --measure-detection-time
```

#### Recovery Time
- **Target**: <10 seconds from UNHEALTHY to ACTIVE
- **Includes**: Health check, state validation, reconnection

**Procedure**:
```bash
# Simulate agent recovery
./load-test recovery --agents=100 --fail-duration=5s \
  --measure-recovery-time
```

#### Acceptance Criteria
- ✓ False positive rate <0.1% across 1-hour test
- ✓ Detection latency within 1.5× interval for 99% of failures
- ✓ Recovery time <10s for 95% of agents

---

### 2.3 E3: Throughput

**Target**: 10,000+ requests/second per gateway with linear scaling

#### Single Gateway
- **Sustained throughput**: 10,000+ req/s
- **Peak burst**: 15,000+ req/s (30 seconds)
- **Mix**: 70% tool invocations, 20% queries, 10% control

**Procedure**:
```bash
# Throughput test with mixed workload
./load-test throughput --target-rps=10000 --duration=10m \
  --tool-invoke=70% --query=20% --control=10%

# Monitor: gateway.requests_per_second, gateway.error_rate
```

#### Horizontal Scaling
- **Target**: Linear scaling to 100,000+ req/s
- **Configuration**: 10 gateway instances behind load balancer
- **Efficiency**: >90% linear scaling (10× gateways → >9× throughput)

**Procedure**:
```bash
# Scale gateways and measure throughput
for gateways in 1 2 4 8 10; do
  kubectl scale deployment pap-gateway --replicas=$gateways
  ./load-test throughput --target-rps=$((10000 * gateways)) \
    --duration=5m --measure-efficiency
done
```

#### Circuit Breaker Activation
- **Target**: <100ms from error threshold to circuit open
- **Threshold**: 5 consecutive errors or 50% error rate over 10s window
- **Recovery**: Exponential backoff (1s, 2s, 4s, 8s, 16s)

**Procedure**:
```bash
# Inject errors and measure circuit breaker response
./load-test circuit-breaker --inject-errors=100% \
  --measure-activation-time
```

#### Acceptance Criteria
- ✓ Single gateway sustains 10,000+ req/s with <1% error rate
- ✓ Horizontal scaling efficiency >90%
- ✓ Circuit breaker activation <100ms, recovery working correctly

---

### 2.4 E4: Ownership Transfer

**Target**: <30 seconds with zero downtime

#### Transfer Duration
- **Total time**: <30 seconds (initiation → completion)
- **Phases**:
  - Transfer initiation: <1s
  - State snapshot: <10s
  - Credential rotation: <5s
  - Dual-connect handoff: <10s
  - Old credential revocation: <4s

**Procedure**:
```bash
# Measure end-to-end transfer time
./load-test ownership-transfer --agents=10 \
  --source-station=station-a --target-station=station-b \
  --measure-phases
```

#### Zero Downtime Verification
- **In-flight requests**: 0 dropped during transfer
- **Service availability**: 100% throughout transfer
- **State consistency**: Pre-transfer hash = post-transfer hash

**Procedure**:
```bash
# Continuous traffic during transfer
./load-test zero-downtime --agent=test-agent \
  --request-rate=10/s --transfer-at=30s --duration=60s

# Measure: requests_dropped, availability_percentage
```

#### Post-Transfer Error Rate
- **Target**: <0.01% (1 in 10,000 operations)
- **Window**: 5 minutes post-transfer
- **Types**: Authentication failures, state inconsistencies

**Procedure**:
```bash
# Monitor post-transfer operations
./load-test post-transfer-validation --agents=10 \
  --operations=10000 --window=5m
```

#### Acceptance Criteria
- ✓ Transfer completes in <30s for agents with <100MB state
- ✓ Zero request drops during transfer
- ✓ Post-transfer error rate <0.01%

---

## 3. Security Validation

### 3.1 Authentication Enforcement

#### mTLS Coverage
- **Target**: 100% of PAP-CP connections
- **Validation**: Reject all non-mTLS connection attempts
- **Test**: 10,000 connection attempts without valid certificates

**Procedure**:
```bash
# Attempt connections without mTLS
./security-test mtls-enforcement --attempts=10000 \
  --expect-rejection=100%
```

#### Signature Verification
- **Target**: 100% of control messages validated
- **Validation**: Reject messages with invalid/missing Ed25519 signatures
- **Test**: 10,000 messages with tampered signatures

**Procedure**:
```bash
# Send control messages with invalid signatures
./security-test signature-validation --messages=10000 \
  --tamper=signature --expect-rejection=100%
```

#### Replay Attack Prevention
- **Target**: Zero successful replays in 10M attempts
- **Validation**: Nonce cache prevents duplicate nonces
- **Test**: Replay captured messages with original nonces

**Procedure**:
```bash
# Capture and replay messages
./security-test replay-prevention --capture-duration=5m \
  --replay-attempts=10000000 --expect-success=0
```

#### Token Expiry Enforcement
- **Target**: 100% compliance
- **Validation**: Reject expired JWT tokens
- **Test**: 1,000 requests with expired tokens

**Procedure**:
```bash
# Generate expired tokens and attempt requests
./security-test token-expiry --requests=1000 \
  --token-age=2h --expect-rejection=100%
```

### 3.2 Audit Completeness

#### Control Operation Logging
- **Target**: 100% of lifecycle events logged
- **Events**: Provision, Invoke, Terminate, Transfer, ForceKill
- **Validation**: Cross-reference agent operations with audit logs

**Procedure**:
```bash
# Execute 1000 lifecycle operations and verify logging
./security-test audit-logging --operations=1000 \
  --verify-completeness=100%
```

#### Tamper Detection
- **Target**: Immutable append-only logs
- **Validation**: Detect any log modification attempts
- **Test**: Attempt to modify/delete 100 log entries

**Procedure**:
```bash
# Attempt log tampering
./security-test tamper-detection --attempts=100 \
  --expect-detection=100%
```

---

## 4. Interoperability Testing

### 4.1 MCP Integration

#### Tool Invocation
- **Scenario**: Invoke 1,000+ MCP server tools via PAP-Hooks
- **Protocols**: WebSocket, HTTP SSE
- **Validation**: Request/response format compliance

**Procedure**:
```bash
# Test MCP tool invocations
./interop-test mcp-tools --servers=10 --invocations=100 \
  --protocol=websocket,sse
```

#### Resource Access
- **Scenario**: Read/write agent memory via MCP resource patterns
- **Validation**: State consistency, versioning

**Procedure**:
```bash
# Test MCP resource patterns
./interop-test mcp-resources --agents=10 --operations=1000
```

### 4.2 A2A Integration

#### Agent Card Discovery
- **Scenario**: Discover 100 agents via Service Registry
- **Validation**: Capability matching, DNS resolution

**Procedure**:
```bash
# Test agent discovery
./interop-test a2a-discovery --agents=100 \
  --validate-capabilities
```

#### Task Delegation
- **Scenario**: Delegate tasks between 50 agent pairs
- **Validation**: Task state transitions, result delivery

**Procedure**:
```bash
# Test A2A delegation workflows
./interop-test a2a-delegation --pairs=50 --tasks=10
```

### 4.3 Framework Compatibility

#### LangChain/LangGraph
- **Scenario**: Run multi-step chains with PAP lifecycle management
- **Validation**: Chain execution, intermediate state preservation

#### CrewAI
- **Scenario**: Multi-agent collaboration with PAP coordination
- **Validation**: Role assignments, task dependencies

#### AutoGPT
- **Scenario**: Autonomous operation with PAP governance
- **Validation**: Goal decomposition, tool usage tracking

---

## 5. Chaos Engineering

### 5.1 Scenarios

#### Network Partitions
- **Injection**: Partition Station from 30% of agents for 60 seconds
- **Expected**: Agents mark Station unreachable, queue operations, reconnect
- **Success**: No data loss, full recovery within 120 seconds

#### Certificate Expiration
- **Injection**: Force certificate expiry during operation
- **Expected**: Automatic rotation via provisioning flow
- **Success**: Zero downtime, all agents re-authenticated

#### Gateway Failures
- **Injection**: Kill 50% of gateway pods
- **Expected**: Traffic rerouted, queued requests retried
- **Success**: <1s disruption, no request loss

#### Agent Process Crashes
- **Injection**: SIGKILL random 10% of agents
- **Expected**: Detection via missed heartbeats, marked KILLED
- **Success**: Detection within 1.5× interval, audit log entry

#### Database Unavailability
- **Injection**: Network partition database for 30 seconds
- **Expected**: Circuit breaker opens, operations cached
- **Success**: Graceful degradation, recovery when available

#### DNS Resolution Failures
- **Injection**: Return NXDOMAIN for agent subdomains
- **Expected**: Fallback to IP addresses, alerts triggered
- **Success**: No complete outages, manual intervention alert

### 5.2 Success Criteria

- ✓ **No silent failures**: All failures logged and alerted
- ✓ **Graceful degradation**: System remains partially operational
- ✓ **Automatic recovery**: Return to normal within SLA (99.9% availability)
- ✓ **Zero data loss**: All committed operations preserved
- ✓ **State consistency**: No orphaned agents or corrupt state

---

## 6. Benchmarking Procedures

### 6.1 Baseline Establishment

1. **Clean environment**: Fresh Kubernetes cluster, no background load
2. **Warmup period**: 5 minutes of steady traffic before measurements
3. **Repetition**: 3 runs per test, report median and 95% CI
4. **Documentation**: Record environment specs, versions, configurations

### 6.2 Load Profiles

#### Steady State
- **Duration**: 10 minutes
- **Profile**: Constant request rate
- **Purpose**: Baseline latency and throughput

#### Spike
- **Duration**: 2 minutes (1min ramp-up, 30s peak, 30s ramp-down)
- **Profile**: 10× normal load
- **Purpose**: Burst handling and recovery

#### Gradual Increase
- **Duration**: 30 minutes
- **Profile**: Linear ramp from 0 to 2× capacity
- **Purpose**: Identify saturation point and degradation curve

### 6.3 Reporting

**Metrics to Report**:
- Throughput: requests/second (mean, P50, P90, P99)
- Latency: milliseconds (P50, P90, P95, P99, P99.9)
- Error rates: percentage by error code
- Resource utilization: CPU, memory, network (per component)
- Availability: percentage uptime during test

**Report Format**:
```markdown
## Benchmark Results: Control Plane Latency

**Environment**: AWS EKS 1.28, 3× m5.4xlarge nodes
**Date**: 2025-11-12
**Version**: PAP v1.0

| Metric | Target | Run 1 | Run 2 | Run 3 | Median | Status |
|--------|--------|-------|-------|-------|--------|--------|
| Heartbeat P50 | <5ms | 3.2ms | 3.4ms | 3.1ms | 3.2ms | ✓ PASS |
| Heartbeat P99 | <20ms | 15.1ms | 16.3ms | 14.8ms | 15.1ms | ✓ PASS |
| Control P50 | <10ms | 8.5ms | 9.1ms | 8.3ms | 8.5ms | ✓ PASS |
| Control P99 | <50ms | 42.3ms | 45.1ms | 43.2ms | 43.2ms | ✓ PASS |

**Notes**: All targets met. P99 latencies increase ~2ms under network jitter.
```

---

## 7. References

### Related Documents
- **Main Specification**: `pap-rfc-001-v1.0.md` - Complete PAP v1.0 protocol specification
- **Deployment Guide**: `deployment-guide.md` - Kubernetes reference deployment
- **Academic Paper**: "The Plugged.in Agent Protocol (PAP)" Draft v0.3 for arXiv cs.DC

### Academic Foundation
For complete academic references, see `references.md`.

Key papers:
- [1] V. de Lamo Castrillo et al., "Fundamentals of Building Autonomous LLM Agents," arXiv:2510.09244, 2025
- [2] Y. He et al., "Security of AI Agents," arXiv:2406.08689v2, 2024

---

**Document Version**: 1.0
**Status**: Benchmarking Guide
**Last Updated**: November 12, 2025
**Protocol Version**: PAP v1.0 (Paper-Aligned)
**Paper Version**: Draft v0.3 (for arXiv cs.DC)
