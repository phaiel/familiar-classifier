use std::env;

#[derive(Debug, Clone)]
pub struct Config {
    pub collection_name: String,
    pub confidence_threshold: f64,
    pub max_alternatives: i32,
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            collection_name: env::var("COLLECTION_NAME")
                .unwrap_or_else(|_| "pattern_index".to_string()),
            confidence_threshold: env::var("CONFIDENCE_THRESHOLD")
                .unwrap_or_else(|_| "0.5".to_string())
                .parse()
                .unwrap_or(0.5),
            max_alternatives: env::var("MAX_ALTERNATIVES")
                .unwrap_or_else(|_| "3".to_string())
                .parse()
                .unwrap_or(3),
        }
    }
} 