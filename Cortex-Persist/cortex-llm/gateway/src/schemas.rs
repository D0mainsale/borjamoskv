use serde::{Deserialize, Serialize};

#[derive(Deserialize, Debug)]
pub struct InferenceRequest {
    pub prompt: String,
    pub system_invariant: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ThermodynamicDelta {
    pub hash_base: String,
    pub confidence: String,
    pub claim: String,
    pub operations: Vec<serde_json::Value>,
    pub raw_exergy: f32,
}

#[derive(Serialize)]
pub struct GatewayResponse {
    pub status: String,
    pub delta: Option<ThermodynamicDelta>,
    pub error: Option<String>,
}

// Ollama API structures
#[derive(Serialize)]
pub struct OllamaRequest {
    pub model: String,
    pub prompt: String,
    pub system: String,
    pub stream: bool,
    pub format: String,
}

#[derive(Deserialize, Debug)]
pub struct OllamaResponse {
    pub response: String,
}
