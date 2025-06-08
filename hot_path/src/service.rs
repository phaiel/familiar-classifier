use uuid::Uuid;
use crate::{
    classifier::HierarchicalClassifier,
    config::Config,
    generated::{ClassificationRequest, PatternMatch},
    stats::StatsTracker,
};
use serde::Serialize;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{info, error};
use axum::{extract::State, Json};
use serde_json;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ApiClassificationResponse {
    pub request_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub match_result: Option<PatternMatch>,
    pub alternatives: Vec<PatternMatch>,
    pub classification_steps: Vec<String>,
    pub processing_time_ms: f64,
    pub status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error_message: Option<String>,
}

#[derive(Clone)]
pub struct ClassificationService {
    classifier: Arc<HierarchicalClassifier>,
    stats: Arc<Mutex<StatsTracker>>,
}

impl ClassificationService {
    pub async fn new(config: Config) -> Result<Self, Box<dyn std::error::Error>> {
        info!("🚀 Initializing classification service...");
        
        let classifier = Arc::new(HierarchicalClassifier::new(config.clone()).await?);
        let stats = Arc::new(Mutex::new(StatsTracker::new()));
        
        info!("✅ Classification service initialized successfully");
        Ok(Self { classifier, stats })
    }
    
    pub async fn classify_hierarchical(&self, request: &ClassificationRequest) -> Result<ApiClassificationResponse, Box<dyn std::error::Error + Send + Sync>> {
        let start_time = std::time::Instant::now();
        let request_id = Uuid::new_v4().to_string();
        
        if request.weave_unit.text.trim().is_empty() {
            let processing_time = start_time.elapsed().as_millis() as f64;
            return Ok(ApiClassificationResponse {
                request_id,
                match_result: None,
                alternatives: vec![],
                classification_steps: vec!["Error: Empty text provided".to_string()],
                processing_time_ms: processing_time,
                status: "error".to_string(),
                error_message: Some("Empty text provided".to_string()),
            });
        }
        
        let (primary_match, alternatives, steps) = self.classifier.classify(
            &request.weave_unit.text,
            request.confidence_threshold.unwrap_or(0.5),
            request.max_alternatives.unwrap_or(3) as usize,
        ).await?;
        
        let processing_time = start_time.elapsed().as_millis() as f64;
        
        self.stats.lock().await.log_request(processing_time);
        
        Ok(ApiClassificationResponse {
            request_id,
            match_result: primary_match,
            alternatives,
            classification_steps: steps,
            processing_time_ms: processing_time,
            status: "success".to_string(),
            error_message: None,
        })
    }
    
    pub async fn reload_patterns(&self) -> Result<Json<serde_json::Value>, Box<dyn std::error::Error>> {
        info!("🔄 Reloading patterns...");
        let patterns_loaded = self.classifier.load_patterns_from_file("assets/patterns_with_embeddings.json").await?;
        let levels_loaded = self.classifier.load_level_schemas("assets/level_schemas_with_embeddings.json").await?;
        
        Ok(Json(serde_json::json!({
            "status": "success",
            "patterns_loaded": patterns_loaded,
            "levels_loaded": levels_loaded
        })))
    }
    
    pub async fn get_status(&self) -> Result<Json<serde_json::Value>, Box<dyn std::error::Error>> {
        let stats = self.stats.lock().await;
        self.classifier.health_check().await?;
        Ok(Json(serde_json::json!({
            "status": "ok",
            "stats": stats.get_summary()
        })))
    }
}

pub mod handlers {
    use super::{ClassificationService, ApiClassificationResponse};
    use axum::{extract::State, Json};
    use crate::generated::ClassificationRequest;
    use tracing::debug;
    use uuid::Uuid;

    pub async fn health_check() -> &'static str { "OK" }

    pub async fn classify_handler(
        State(service): State<ClassificationService>,
        Json(request): Json<ClassificationRequest>,
    ) -> Json<ApiClassificationResponse> {
        debug!("Received classification request: {:?}", request);
        match service.classify_hierarchical(&request).await {
            Ok(response) => Json(response),
            Err(e) => {
                Json(ApiClassificationResponse {
                    request_id: Uuid::new_v4().to_string(),
                    match_result: None,
                    alternatives: vec![],
                    classification_steps: vec![e.to_string()],
                    processing_time_ms: 0.0,
                    status: "error".to_string(),
                    error_message: Some(e.to_string()),
                })
            }
        }
    }

    pub async fn status_handler(
        State(service): State<ClassificationService>,
    ) -> Result<Json<serde_json::Value>, axum::http::StatusCode> {
        service.get_status().await.map_err(|_| axum::http::StatusCode::INTERNAL_SERVER_ERROR)
    }

    pub async fn reload_patterns_handler(
        State(service): State<ClassificationService>,
    ) -> Result<Json<serde_json::Value>, axum::http::StatusCode> {
        service.reload_patterns().await.map_err(|_| axum::http::StatusCode::INTERNAL_SERVER_ERROR)
    }
} 