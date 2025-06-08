use axum::{routing::{get, post}, Router};
use tokio::net::TcpListener;
use tracing::info;
use familiar_pattern_classifier::{
    config::Config,
    service::{
        ClassificationService,
        handlers::{
            health_check,
            classify_handler,
            status_handler,
            reload_patterns_handler
        },
    },
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    info!("🚀 Starting Pattern Classifier Hot Path Service");

    let config = Config::from_env();
    info!("📋 Configuration loaded");

    let service = ClassificationService::new(config.clone()).await?;
    
    let app = Router::new()
        .route("/", get(health_check))
        .route("/health", get(health_check))
        .route("/classify", post(classify_handler))
        .route("/status", get(status_handler))
        .route("/reload-patterns", post(reload_patterns_handler))
        .with_state(service);
        
    let addr = format!("0.0.0.0:{}", config.port);
    info!("🚀 Server listening on {}", addr);
    
    let listener = TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;
    
    Ok(())
}