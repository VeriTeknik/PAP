from datetime import datetime
from uuid import uuid4

from pap.envelope import (
    AgentIdentity,
    AuthContext,
    Envelope,
    Event,
    EventType,
    Heartbeat,
    MetricBatch,
    MetricPoint,
)


def make_auth() -> AuthContext:
    # Demo-only placeholder values
    return AuthContext(
        signature=b"demo",
        algorithm="ed25519",
        payload_hash=b"demo",
        nonce=str(uuid4()),
        issued_at=datetime.utcnow(),
    )


def heartbeat_envelope() -> Envelope:
    hb = Heartbeat(cpu_percent=3.2, memory_mb=256.4, uptime_seconds=120.0, active_jobs=0)
    evt = Event(event_type=EventType.HEARTBEAT, heartbeat=hb)
    env = Envelope(
        message_id=str(uuid4()),
        sent_at=datetime.utcnow(),
        sender=AgentIdentity(agent="focus", cluster="cluster-a"),
        auth=make_auth(),
        body=evt,
        # Attach tracing IDs for correlation
        trace_id="0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
        span_id="abcdef12abcdef12",
    )
    return env


def metrics_envelope() -> Envelope:
    points = [
        MetricPoint(name="jobs.completed", value=1.0, observed_at=datetime.utcnow(), attributes={"agent": "focus"}),
        MetricPoint(name="latency.ms", value=25.4, observed_at=datetime.utcnow(), attributes={"route": "analyze"}),
    ]
    batch = MetricBatch(points=points)
    evt = Event(event_type=EventType.METRIC, metrics=batch)
    env = Envelope(
        message_id=str(uuid4()),
        sent_at=datetime.utcnow(),
        sender=AgentIdentity(agent="focus", cluster="cluster-a"),
        auth=make_auth(),
        body=evt,
        trace_id="0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
        span_id="1234567812345678",
    )
    return env


if __name__ == "__main__":
    hb = heartbeat_envelope()
    mx = metrics_envelope()
    # In a real client, these would be serialized and sent to the Proxy
    print("Heartbeat envelope:", hb)
    print("Metrics envelope:", mx)

