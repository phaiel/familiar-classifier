use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, warn, error};
use serde_json;

use crate::generated::*;
use crate::config::Config;
use crate::classifier::PatternClassifier;

#[derive(Clone)]
pub struct ClassificationService {
    classifier: Arc<PatternClassifier>,
    config: Config,
    stats: Arc<RwLock<ServiceStats>>,
}

#[derive(Debug, Default)]
struct ServiceStats {
    requests_processed: u64,
    total_processing_time_ms: f64,
    errors: u64,
}

impl ClassificationService {
    pub async fn new(config: Config) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        info!("🔧 Initializing Classification Service");
        
        let classifier = Arc::new(PatternClassifier::new(config.clone()).await?);
        
        let service = Self {
            classifier,
            config,
            stats: Arc::new(RwLock::new(ServiceStats::default())),
        };
        
        info!("✅ Classification Service initialized");
        Ok(service)
    }

    pub async fn classify(&self, request: &ClassificationRequest) -> Result<ClassificationResponse, Box<dyn std::error::Error + Send + Sync>> {
        let start_time = std::time::Instant::now();
        
        // Validate request
        if request.weave_unit.text.trim().is_empty() {
            let processing_time = start_time.elapsed().as_millis() as f64;
            return Ok(ClassificationResponse::error(
                "Empty text provided".to_string(),
                processing_time
            ));
        }
        
        // Perform classification
        let result = self.classifier.classify(
            &request.weave_unit.text,
            request.confidence_threshold,
            request.max_alternatives as usize,
            request.filter_by_domain.as_deref(),
        ).await;
        
        let processing_time = start_time.elapsed().as_millis() as f64;
        
        // Update stats
        self.update_stats(processing_time, result.is_ok()).await;
        
        match result {
            Ok((primary_match, alternatives)) => {
                Ok(ClassificationResponse::success(
                    primary_match,
                    alternatives,
                    processing_time
                ))
            },
            Err(e) => {
                error!("Classification failed: {}", e);
                Ok(ClassificationResponse::error(
                    format!("Classification error: {}", e),
                    processing_time
                ))
            }
        }
    }

    pub async fn get_status(&self) -> serde_json::Value {
        let stats = self.stats.read().await;
        let vector_store_healthy = self.check_vector_store_health().await;
        let vector_store_stats = self.classifier.get_stats().await.unwrap_or_else(|_| serde_json::json!({}));
        
        serde_json::json!({
            "service": "pattern-classifier-hot-path",
            "status": if vector_store_healthy { "healthy" } else { "degraded" },
            "vector_store_connection": vector_store_healthy,
            "config": {
                "collection": self.config.collection_name,
                "confidence_threshold": self.config.confidence_threshold,
                "max_alternatives": self.config.max_alternatives
            },
            "runtime_stats": {
                "requests_processed": stats.requests_processed,
                "average_processing_time_ms": if stats.requests_processed > 0 {
                    stats.total_processing_time_ms / stats.requests_processed as f64
                } else { 0.0 },
                "errors": stats.errors,
                "error_rate": if stats.requests_processed > 0 {
                    stats.errors as f64 / stats.requests_processed as f64
                } else { 0.0 }
            },
            "vector_store_stats": vector_store_stats
        })
    }

    async fn update_stats(&self, processing_time_ms: f64, success: bool) {
        let mut stats = self.stats.write().await;
        stats.requests_processed += 1;
        stats.total_processing_time_ms += processing_time_ms;
        if !success {
            stats.errors += 1;
        }
    }

    async fn check_vector_store_health(&self) -> bool {
        match self.classifier.health_check().await {
            Ok(_) => true,
            Err(_) => false,
        }
    }
    
    /// Reload patterns from file
    pub async fn reload_patterns(&self, file_path: Option<String>) -> Result<serde_json::Value, Box<dyn std::error::Error + Send + Sync>> {
        let path = file_path.unwrap_or_else(|| "assets/patterns_with_embeddings.json".to_string());
        
        info!("🔄 Reloading patterns from: {}", path);
        
        match self.classifier.load_patterns_from_file(&path).await {
            Ok(count) => {
                info!("✅ Successfully reloaded {} patterns", count);
                Ok(serde_json::json!({
                    "status": "success",
                    "message": format!("Reloaded {} patterns from {}", count, path),
                    "patterns_loaded": count,
                    "file_path": path
                }))
            },
            Err(e) => {
                error!("❌ Failed to reload patterns: {}", e);
                Err(format!("Failed to reload patterns: {}", e).into())
            }
        }
    }
} 