// Generated types for Pattern Classifier Hot Path
// DO NOT EDIT - regenerated on every build

use serde::{Serialize, Deserialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::collections::HashMap;

// Core enums from cold path
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PatternMixin {
    Time,
    Emotion,
    ThreadLink,
    Location,
    Person,
    Activity,
    Health,
    Development,
}

// Input for classification
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WeaveUnit {
    #[serde(default)]
    pub id: Option<Uuid>,
    pub text: String,
    #[serde(default)]
    pub metadata: HashMap<String, serde_json::Value>,
    #[serde(default)]
    pub timestamp: Option<String>,
}

// Pattern definition
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PatternSchema {
    pub id: String,
    pub description: String,
    #[serde(default)]
    pub mixins: Vec<PatternMixin>,
    pub sample_texts: Vec<String>,
    #[serde(default)]
    pub domain: Option<String>,
    #[serde(default)]
    pub category: Option<String>,
    #[serde(default)]
    pub metadata: HashMap<String, serde_json::Value>,
}

// Classification result
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PatternMatch {
    pub pattern_id: String,
    pub confidence: f64,
    #[serde(default)]
    pub alternatives: Vec<HashMap<String, serde_json::Value>>,
    #[serde(default)]
    pub embedding_vector: Option<Vec<f32>>,
    #[serde(default)]
    pub metadata: HashMap<String, serde_json::Value>,
}

// API request/response
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ClassificationRequest {
    pub weave_unit: WeaveUnit,
    #[serde(default = "default_max_alternatives")]
    pub max_alternatives: i32,
    #[serde(default = "default_confidence_threshold")]
    pub confidence_threshold: f64,
    #[serde(default)]
    pub filter_by_domain: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ClassificationResponse {
    #[serde(default)]
    pub request_id: Option<Uuid>,
    #[serde(default)]
    pub match_result: Option<PatternMatch>,
    #[serde(default)]
    pub alternatives: Vec<PatternMatch>,
    pub processing_time_ms: f64,
    #[serde(default = "default_status")]
    pub status: String,
    #[serde(default)]
    pub error_message: Option<String>,
}

// Configuration
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct IndexBuildConfig {
    #[serde(default = "default_model_name")]
    pub model_name: String,
    #[serde(default = "default_qdrant_host")]
    pub qdrant_host: String,
    #[serde(default = "default_qdrant_port")]
    pub qdrant_port: i32,
    #[serde(default = "default_collection_name")]
    pub collection_name: String,
    #[serde(default = "default_vector_size")]
    pub vector_size: i32,
    #[serde(default = "default_patterns_dir")]
    pub patterns_dir: String,
    #[serde(default = "default_batch_size")]
    pub batch_size: i32,
    #[serde(default)]
    pub overwrite_collection: bool,
}

// Helper functions for defaults
fn default_max_alternatives() -> i32 { 3 }
fn default_confidence_threshold() -> f64 { 0.5 }
fn default_status() -> String { "success".to_string() }
fn default_model_name() -> String { "all-MiniLM-L6-v2".to_string() }
fn default_qdrant_host() -> String { "localhost".to_string() }
fn default_qdrant_port() -> i32 { 6333 }
fn default_collection_name() -> String { "pattern_index".to_string() }
fn default_vector_size() -> i32 { 384 }
fn default_patterns_dir() -> String { "cold_path/patterns".to_string() }
fn default_batch_size() -> i32 { 100 }

// Implementations for generated types (like ECS Familiar)
impl WeaveUnit {
    /// Create a new WeaveUnit with generated ID and timestamp
    pub fn new(text: String) -> Self {
        Self {
            id: Some(Uuid::new_v4()),
            text,
            metadata: HashMap::new(),
            timestamp: Some(chrono::Utc::now().to_rfc3339()),
        }
    }

    /// Check if this WeaveUnit was created recently
    pub fn is_recent(&self) -> bool {
        if let Some(timestamp_str) = &self.timestamp {
            if let Ok(timestamp) = chrono::DateTime::parse_from_rfc3339(timestamp_str) {
                let now = chrono::Utc::now();
                let duration = now.signed_duration_since(timestamp.with_timezone(&chrono::Utc));
                return duration.num_minutes() < 30; // Recent if within 30 minutes
            }
        }
        false
    }

    /// Get text length for validation
    pub fn text_length(&self) -> usize {
        self.text.len()
    }
}

impl PatternMatch {
    /// Create a new pattern match
    pub fn new(pattern_id: String, confidence: f64) -> Self {
        Self {
            pattern_id,
            confidence,
            alternatives: Vec::new(),
            embedding_vector: None,
            metadata: HashMap::new(),
        }
    }

    /// Check if confidence is above threshold
    pub fn is_confident(&self, threshold: f64) -> bool {
        self.confidence >= threshold
    }

    /// Get domain from pattern ID
    pub fn get_domain(&self) -> Option<String> {
        self.pattern_id.split('/').next().map(|s| s.to_string())
    }
}

impl ClassificationRequest {
    /// Create a simple classification request
    pub fn new(text: String) -> Self {
        Self {
            weave_unit: WeaveUnit::new(text),
            max_alternatives: default_max_alternatives(),
            confidence_threshold: default_confidence_threshold(),
            filter_by_domain: None,
        }
    }

    /// Create with domain filter
    pub fn with_domain(text: String, domain: String) -> Self {
        Self {
            weave_unit: WeaveUnit::new(text),
            max_alternatives: default_max_alternatives(),
            confidence_threshold: default_confidence_threshold(),
            filter_by_domain: Some(domain),
        }
    }
}

impl ClassificationResponse {
    /// Create a successful response
    pub fn success(
        pattern_match: Option<PatternMatch>,
        alternatives: Vec<PatternMatch>,
        processing_time_ms: f64,
    ) -> Self {
        Self {
            request_id: Some(Uuid::new_v4()),
            match_result: pattern_match,
            alternatives,
            processing_time_ms,
            status: default_status(),
            error_message: None,
        }
    }

    /// Create an error response
    pub fn error(error_message: String, processing_time_ms: f64) -> Self {
        Self {
            request_id: Some(Uuid::new_v4()),
            match_result: None,
            alternatives: Vec::new(),
            processing_time_ms,
            status: "error".to_string(),
            error_message: Some(error_message),
        }
    }

    /// Check if response was successful
    pub fn is_success(&self) -> bool {
        self.status == "success"
    }
}

impl Default for PatternMixin {
    fn default() -> Self {
        Self::Time
    }
} 