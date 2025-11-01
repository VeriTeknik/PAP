from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence


class PapErrorCode(str, Enum):
    OK = "OK"
    ACCEPTED = "ACCEPTED"
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    AGENT_UNHEALTHY = "AGENT_UNHEALTHY"
    AGENT_BUSY = "AGENT_BUSY"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    PROXY_ERROR = "PROXY_ERROR"
    VERSION_UNSUPPORTED = "VERSION_UNSUPPORTED"


class ControlType(str, Enum):
    TERMINATE = "terminate"
    FORCE_KILL = "force_kill"
    PAUSE = "pause"
    RESUME = "resume"
    PING = "ping"


class EventType(str, Enum):
    HEARTBEAT = "heartbeat"
    LOG = "log"
    ALERT = "alert"
    METRIC = "metric"


@dataclass(frozen=True)
class AgentIdentity:
    agent: str
    cluster: str
    version: Optional[str] = None
    instance: Optional[str] = None


@dataclass
class AuthContext:
    signature: bytes
    algorithm: str
    payload_hash: bytes
    nonce: str
    issued_at: datetime


@dataclass
class Target:
    agent: str
    namespace: Optional[str] = None
    capability: Optional[str] = None


@dataclass
class Invoke:
    target: Target
    method: str
    arguments: Optional[MutableMapping[str, Any]] = None
    deadline: Optional[datetime] = None
    expect_reply: bool = True
    metadata: Optional[MutableMapping[str, str]] = None


@dataclass
class OutputChunk:
    content_type: str
    data: bytes
    annotations: Optional[MutableMapping[str, Any]] = None


@dataclass
class Response:
    status: PapErrorCode
    outputs: List[OutputChunk] = field(default_factory=list)
    metadata: Optional[MutableMapping[str, str]] = None
    is_final: bool = True


@dataclass
class Heartbeat:
    cpu_percent: float
    memory_mb: float
    uptime_seconds: float
    active_jobs: int
    gauges: Optional[MutableMapping[str, float]] = None


@dataclass
class LogEvent:
    level: str
    message: str
    fields: Optional[MutableMapping[str, Any]] = None


@dataclass
class AlertEvent:
    title: str
    description: str
    severity: str
    labels: Optional[MutableMapping[str, Any]] = None


@dataclass
class MetricPoint:
    name: str
    value: float
    observed_at: datetime
    attributes: Optional[MutableMapping[str, str]] = None


@dataclass
class MetricBatch:
    points: Sequence[MetricPoint]


@dataclass
class Event:
    event_type: EventType
    context: Optional[MutableMapping[str, Any]] = None
    heartbeat: Optional[Heartbeat] = None
    log: Optional[LogEvent] = None
    alert: Optional[AlertEvent] = None
    metrics: Optional[MetricBatch] = None


@dataclass
class ErrorPayload:
    code: PapErrorCode
    message: str
    recoverable: bool = False
    details: Optional[MutableMapping[str, Any]] = None


@dataclass
class ControlDirective:
    control_type: ControlType
    arguments: Optional[MutableMapping[str, Any]] = None
    enforce_at: Optional[datetime] = None


@dataclass
class HandshakeAck:
    accepted: bool
    reason: Optional[str] = None


@dataclass
class Envelope:
    message_id: str
    sent_at: datetime
    sender: AgentIdentity
    auth: AuthContext
    body: Any
    parent_id: Optional[str] = None
    correlation_id: Optional[str] = None
    annotations: Optional[Mapping[str, str]] = None
    # OpenTelemetry-compatible identifiers (hex)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
