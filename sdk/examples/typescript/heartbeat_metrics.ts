// Minimal example showing heartbeat (liveness-only) and separate metrics emission
import type {
  AgentIdentity,
  AuthContext,
  EventMessage,
  Heartbeat,
  MetricBatch,
  PapEnvelope,
} from "../typescript/src/index";

function auth(): AuthContext {
  return {
    signature: new Uint8Array([1, 2, 3]),
    algorithm: "ed25519",
    payloadHash: new Uint8Array([4, 5, 6]),
    nonce: crypto.randomUUID(),
    issuedAt: new Date(),
  };
}

const sender: AgentIdentity = { agent: "focus", cluster: "cluster-a" };

export function heartbeatEnvelope(): PapEnvelope<EventMessage> {
  const hb: Heartbeat = {
    cpuPercent: 2.1,
    memoryMb: 128.5,
    uptimeSeconds: 90,
    activeJobs: 0,
  };
  const event: EventMessage = { kind: "event", eventType: "heartbeat", detail: hb };
  return {
    messageId: crypto.randomUUID(),
    sentAt: new Date(),
    sender,
    auth: auth(),
    body: event,
    traceId: "0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
    spanId: "abcdef12abcdef12",
  };
}

export function metricsEnvelope(): PapEnvelope<EventMessage> {
  const metrics: MetricBatch = {
    points: [
      { name: "jobs.completed", value: 1, observedAt: new Date(), attributes: { agent: "focus" } },
      { name: "latency.ms", value: 23.7, observedAt: new Date(), attributes: { route: "analyze" } },
    ],
  };
  const event: EventMessage = { kind: "event", eventType: "metric", detail: metrics };
  return {
    messageId: crypto.randomUUID(),
    sentAt: new Date(),
    sender,
    auth: auth(),
    body: event,
    traceId: "0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
    spanId: "1234567812345678",
  };
}

// Demo output when run under a TS runtime supporting `crypto.randomUUID()`
console.log("Heartbeat:", heartbeatEnvelope());
console.log("Metrics:", metricsEnvelope());

