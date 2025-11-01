package pap

import (
	"time"

	"github.com/google/uuid"
)

// Envelope wraps every PAP message exchanged between Station and Satellite.
type Envelope struct {
    MessageID     string
    ParentID      string
    CorrelationID string
    SentAt        time.Time
    Sender        AgentIdentity
    Auth          AuthContext
    Annotations   map[string]string
    Body          MessageBody
    // OpenTelemetry-compatible identifiers
    TraceID string
    SpanID  string
}

// AgentIdentity describes the logical and infrastructure placement of an agent.
type AgentIdentity struct {
	Agent    string
	Cluster  string
	Version  string
	Instance string
}

// AuthContext provides signature material for verifying envelopes.
type AuthContext struct {
	Signature   []byte
	Algorithm   string
	PayloadHash []byte
	Nonce       string
	IssuedAt    time.Time
}

// MessageBody enumerates the supported payload families.
type MessageBody interface {
	isMessageBody()
}

// InvokePayload represents a command issued to an agent.
type InvokePayload struct{}

func (InvokePayload) isMessageBody() {}

// ControlPayload represents lifecycle directives like terminate or pause.
type ControlPayload struct{}

func (ControlPayload) isMessageBody() {}

// NewEnvelope seeds an envelope with a freshly generated UUID.
func NewEnvelope(sender AgentIdentity, auth AuthContext, body MessageBody) Envelope {
	return Envelope{
		MessageID:   uuid.NewString(),
		SentAt:      time.Now().UTC(),
		Sender:      sender,
		Auth:        auth,
		Annotations: map[string]string{},
		Body:        body,
	}
}
