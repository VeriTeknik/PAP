//! Core data structures for the Plugged.in Agent Protocol.

use std::collections::BTreeMap;
use std::time::SystemTime;

/// Represents the identity of a Satellite or Station participating in PAP.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AgentIdentity {
    pub agent: String,
    pub cluster: String,
    pub version: Option<String>,
    pub instance: Option<String>,
}

/// Describes the authentication metadata attached to every message envelope.
#[derive(Debug, Clone)]
pub struct AuthContext {
    pub signature: Vec<u8>,
    pub algorithm: String,
    pub payload_hash: Vec<u8>,
    pub nonce: String,
    pub issued_at: SystemTime,
}

/// Wrapper around all PAP messages.
#[derive(Debug, Clone)]
pub struct Envelope {
    pub message_id: String,
    pub parent_id: Option<String>,
    pub correlation_id: Option<String>,
    pub sent_at: SystemTime,
    pub sender: AgentIdentity,
    pub auth: AuthContext,
    pub annotations: BTreeMap<String, String>,
    pub body: MessageBody,
}

/// Enumeration of supported message families.
#[derive(Debug, Clone)]
pub enum MessageBody {
    Invoke,
    Response,
    Event,
    Error,
    Control,
    HandshakeAck,
}

impl Envelope {
    /// Creates a new envelope with default annotations.
    pub fn new(message_id: String, sender: AgentIdentity, auth: AuthContext, body: MessageBody) -> Self {
        Self {
            message_id,
            parent_id: None,
            correlation_id: None,
            sent_at: SystemTime::now(),
            sender,
            auth,
            annotations: BTreeMap::new(),
            body,
        }
    }
}
