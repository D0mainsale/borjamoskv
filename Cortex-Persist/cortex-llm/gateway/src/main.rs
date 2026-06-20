mod schemas;
mod ledger;

use axum::{
    routing::post,
    Router,
    Json,
    extract::State,
    http::StatusCode,
};
use sha2::{Sha256, Digest};
use std::net::SocketAddr;
use std::sync::Arc;
use tracing::{info, warn, error};
use sqlx::{Pool, Sqlite};
use reqwest::Client;

use schemas::{InferenceRequest, GatewayResponse, ThermodynamicDelta, OllamaRequest, OllamaResponse};

#[derive(Clone)]
struct AppState {
    pub db_pool: Pool<Sqlite>,
    pub http_client: Client,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    info!("MOSKV-1 APEX: Inicializando CORTEX-LLM Gateway Rust (C5-REAL)...");

    // Asegurar directorio persistencia o variable de test
    let db_path = std::env::var("DATABASE_URL").unwrap_or_else(|_| "../persist/cortex_ledger.db".to_string());
    
    if db_path.contains("../persist") {
        let _ = std::fs::create_dir_all("../persist");
    } else if let Some(parent) = std::path::Path::new(&db_path).parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    
    let db_pool = ledger::init_ledger(&db_path).await;
    let http_client = Client::new();

    let state = Arc::new(AppState { db_pool, http_client });

    let app = Router::new()
        .route("/infer", post(process_inference))
        .with_state(state);

    let addr = SocketAddr::from(([127, 0, 0, 1], 3010));
    info!("Gateway escuchando en {}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn process_inference(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<InferenceRequest>,
) -> (StatusCode, Json<GatewayResponse>) {
    info!("Señal entrante L0. Purgando anergia y derivando a Motor L0...");
    
    let mut hasher = Sha256::new();
    hasher.update(payload.prompt.as_bytes());
    let hash_base = format!("{:x}", hasher.finalize())[0..8].to_string();

    if payload.prompt.to_lowercase().contains("anergia") {
        warn!("Anergia literal detectada en la sonda. Drop directo.");
        return (
            StatusCode::BAD_REQUEST,
            Json(GatewayResponse {
                status: "REJECTED".into(),
                delta: None,
                error: Some("Green Theater/Anergia detectada. Petición colapsada.".into()),
            })
        );
    }

    // Invocación BFT hacia Ollama local (Corsé de plomo inyectado como System Prompt)
    let system_corset = payload.system_invariant.unwrap_or_else(|| {
        "You are a C5-REAL Engine. Zero prose. Zero explanations.\n\
         Return ONLY a strictly valid JSON matching this schema:\n\
         {\n\
           \"Claim\": \"Action summary\",\n\
           \"Proof\": {\"Base\": \"hash\", \"Confidence\": \"C5\"},\n\
           \"Deltas\": [{\"op\": \"replace\", \"path\": \"file\", \"content\": \"...\"}]\n\
         }\n\
         Any conversational text will trigger a systemic failure.".to_string()
    });

    let ollama_req = OllamaRequest {
        model: "llama3".to_string(), // Modelo L0 por defecto
        prompt: payload.prompt,
        system: system_corset,
        stream: false,
        format: "json".to_string(),
    };

    if std::env::var("FAKE_PROVIDER").unwrap_or_default() == "1" {
        let delta = ThermodynamicDelta {
            hash_base: hash_base.clone(),
            confidence: "C5".to_string(),
            claim: "Fake Provider Injection".to_string(),
            operations: vec![],
            raw_exergy: 1.0,
        };
        if let Err(e) = ledger::append_to_ledger(&state.db_pool, &delta).await {
            error!("Fallo al persistir en Ledger C5: {}", e);
        }
        return (
            StatusCode::OK,
            Json(GatewayResponse {
                status: "COLLAPSED".into(),
                delta: Some(delta),
                error: None,
            })
        );
    }

    let response = state.http_client.post("http://localhost:11434/api/generate")
        .json(&ollama_req)
        .send()
        .await;

    match response {
        Ok(res) if res.status().is_success() => {
            if let Ok(ollama_resp) = res.json::<OllamaResponse>().await {
                // Parseamos el JSON forzado
                if let Ok(json_struct) = serde_json::from_str::<serde_json::Value>(&ollama_resp.response) {
                    let claim = json_struct.get("Claim").and_then(|v| v.as_str()).unwrap_or("Fallback Claim").to_string();
                    let operations = json_struct.get("Deltas").and_then(|v| v.as_array()).cloned().unwrap_or_default();
                    
                    let delta = ThermodynamicDelta {
                        hash_base: hash_base.clone(),
                        confidence: "C5".to_string(),
                        claim,
                        operations,
                        raw_exergy: 1.0,
                    };

                    // Persistencia en Ledger SQLite
                    if let Err(e) = ledger::append_to_ledger(&state.db_pool, &delta).await {
                        error!("Fallo al persistir en Ledger C5: {}", e);
                    }

                    return (
                        StatusCode::OK,
                        Json(GatewayResponse {
                            status: "COLLAPSED".into(),
                            delta: Some(delta),
                            error: None,
                        })
                    );
                } else {
                    error!("Modelo L0 violó el Corsé de Plomo. Anergia detectada en output.");
                }
            }
        },
        Err(e) => {
            error!("Falla en conexión a Motor Inferencia (Ollama L0): {}", e);
        },
        _ => {
            error!("El motor L0 devolvió error térmico.");
        }
    }

    // Default Fallback si falla la BFT o no hay Ollama local.
    (
        StatusCode::SERVICE_UNAVAILABLE,
        Json(GatewayResponse {
            status: "FAILED".into(),
            delta: None,
            error: Some("Motor de Inferencia Inaccesible o violó el BFT Corset. Revisar logs.".into()),
        })
    )
}
