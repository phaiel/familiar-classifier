mod generated;
mod config;
mod embeddings;
mod classifier;
mod service;

use axum::{
    routing::{get, post},
    Router, Json,
};
use serde::{Deserialize, Serialize};
use tokio;
use tracing::{info, warn};
use tracing_subscriber;

use crate::generated::*;
use crate::service::ClassificationService;

#[derive(Serialize, Deserialize)]
struct ReloadPatternsRequest {
    file_path: Option<String>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // Initialize tracing
    tracing_subscriber::fmt::init();
    
    info!("🚀 Starting Pattern Classifier Hot Path Service");
    
    // Load configuration
    let config = config::Config::from_env();
    info!("📋 Configuration loaded - collection: {}", config.collection_name);
    
    // Initialize classification service
    let service = match ClassificationService::new(config).await {
        Ok(s) => s,
        Err(e) => {
            warn!("❌ Failed to initialize service: {}", e);
            return Err(e);
        }
    };
    
    // Build our application with routes
    let app = Router::new()
        .route("/", get(health_check))
        .route("/health", get(health_check))
        .route("/classify", post(classify_handler))
        .route("/status", get(status_handler))
        .route("/reload-patterns", post(reload_patterns_handler))
        .with_state(service);
    
    // Run the server
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    info!("🌐 Server listening on http://0.0.0.0:3000");
    
    axum::serve(listener, app).await?;
    
    Ok(())
}

async fn health_check() -> &'static str {
    "OK"
}

async fn classify_handler(
    axum::extract::State(service): axum::extract::State<ClassificationService>,
    Json(request): Json<ClassificationRequest>
) -> Json<ClassificationResponse> {
    let start_time = std::time::Instant::now();
    
    match service.classify(&request).await {
        Ok(response) => Json(response),
        Err(e) => {
            let processing_time = start_time.elapsed().as_millis() as f64;
            Json(ClassificationResponse::error(
                format!("Classification failed: {}", e),
                processing_time
            ))
        }
    }
}

async fn status_handler(
    axum::extract::State(service): axum::extract::State<ClassificationService>
) -> Json<serde_json::Value> {
    let status = service.get_status().await;
    Json(status)
}

async fn reload_patterns_handler(
    axum::extract::State(service): axum::extract::State<ClassificationService>,
    Json(request): Json<ReloadPatternsRequest>
) -> Json<serde_json::Value> {
    match service.reload_patterns(request.file_path).await {
        Ok(response) => Json(response),
        Err(e) => Json(serde_json::json!({
            "status": "error",
            "message": format!("Failed to reload patterns: {}", e)
        }))
    }
} 