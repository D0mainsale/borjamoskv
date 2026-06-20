use sqlx::{sqlite::SqlitePoolOptions, Pool, Sqlite};
use std::path::Path;
use tracing::info;

pub async fn init_ledger(db_path: &str) -> Pool<Sqlite> {
    if !Path::new(db_path).exists() {
        // En SQLite, sqlx necesita que el archivo exista o use sqlite::SqliteConnectOptions
        std::fs::File::create(db_path).unwrap();
    }
    
    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect(&format!("sqlite://{}", db_path))
        .await
        .expect("CORTEX-LLM: Fallo crítico al instanciar el Ledger.");

    sqlx::query(
        "CREATE TABLE IF NOT EXISTS ledger_log (
            id TEXT PRIMARY KEY,
            hash_base TEXT NOT NULL,
            confidence TEXT NOT NULL,
            claim TEXT NOT NULL,
            operations_json TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );"
    )
    .execute(&pool)
    .await
    .expect("Fallo al forjar estructura de base de datos del Ledger.");

    info!("Ledger termodinámico inicializado exitosamente en {}", db_path);
    pool
}

pub async fn append_to_ledger(pool: &Pool<Sqlite>, delta: &crate::schemas::ThermodynamicDelta) -> Result<(), sqlx::Error> {
    let id = uuid::Uuid::new_v4().to_string();
    let ops_json = serde_json::to_string(&delta.operations).unwrap_or_else(|_| "[]".to_string());
    
    sqlx::query(
        "INSERT INTO ledger_log (id, hash_base, confidence, claim, operations_json) VALUES (?, ?, ?, ?, ?)"
    )
    .bind(id)
    .bind(&delta.hash_base)
    .bind(&delta.confidence)
    .bind(&delta.claim)
    .bind(ops_json)
    .execute(pool)
    .await?;

    Ok(())
}
