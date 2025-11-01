export type PapMessageType =
  | "invoke"
  | "response"
  | "event"
  | "error"
  | "control"
  | "handshake_ack";

export interface AgentIdentity {
  agent: string;
  cluster: string;
  version?: string;
  instance?: string;
}

export interface AuthContext {
  signature: Uint8Array;
  algorithm: "ed25519" | "ecdsa-p256" | string;
  payloadHash: Uint8Array;
  nonce: string;
  issuedAt: Date;
}

export interface PapEnvelope<T extends PapMessage> {
  messageId: string;
  parentId?: string;
  correlationId?: string;
  sentAt: Date;
  sender: AgentIdentity;
  auth: AuthContext;
  annotations?: Record<string, string>;
  body: T;
  // OpenTelemetry-compatible identifiers (hex strings)
  traceId?: string;
  spanId?: string;
}

export type PapMessage =
  | InvokeMessage
  | ResponseMessage
  | EventMessage
  | ErrorMessage
  | ControlDirective
  | HandshakeAck;

export interface InvokeMessage {
  kind: "invoke";
  target: Target;
  method: string;
  arguments?: Record<string, unknown>;
  deadline?: Date;
  expectReply?: boolean;
  metadata?: Record<string, string>;
}

export interface Target {
  agent: string;
  namespace?: string;
  capability?: string;
}

export interface ResponseMessage {
  kind: "response";
  status: PapErrorCode;
  outputs?: OutputChunk[];
  metadata?: Record<string, string>;
  isFinal?: boolean;
}

export interface OutputChunk {
  contentType: string;
  data: Uint8Array;
  annotations?: Record<string, unknown>;
}

export interface EventMessage {
  kind: "event";
  eventType: EventType;
  context?: Record<string, unknown>;
  detail?: Heartbeat | LogEvent | AlertEvent | MetricBatch;
}

export type EventType = "heartbeat" | "log" | "alert" | "metric";

export interface Heartbeat {
  cpuPercent: number;
  memoryMb: number;
  uptimeSeconds: number;
  activeJobs: number;
  gauges?: Record<string, number>;
}

export interface LogEvent {
  level: "TRACE" | "DEBUG" | "INFO" | "WARN" | "ERROR";
  message: string;
  fields?: Record<string, unknown>;
}

export interface AlertEvent {
  title: string;
  description: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  labels?: Record<string, unknown>;
}

export interface MetricBatch {
  points: MetricPoint[];
}

export interface MetricPoint {
  name: string;
  value: number;
  observedAt: Date;
  attributes?: Record<string, string>;
}

export interface ErrorMessage {
  kind: "error";
  code: PapErrorCode;
  message: string;
  recoverable?: boolean;
  details?: Record<string, unknown>;
}

export interface ControlDirective {
  kind: "control";
  controlType: ControlType;
  arguments?: Record<string, unknown>;
  enforceAt?: Date;
}

export type ControlType =
  | "terminate"
  | "force_kill"
  | "pause"
  | "resume"
  | "ping";

export interface HandshakeAck {
  kind: "handshake_ack";
  accepted: boolean;
  reason?: string;
}

export type PapErrorCode =
  | "OK"
  | "ACCEPTED"
  | "BAD_REQUEST"
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "TIMEOUT"
  | "CONFLICT"
  | "RATE_LIMITED"
  | "AGENT_UNHEALTHY"
  | "AGENT_BUSY"
  | "DEPENDENCY_FAILED"
  | "INTERNAL_ERROR"
  | "PROXY_ERROR"
  | "VERSION_UNSUPPORTED";

export function now(): Date {
  return new Date();
}
