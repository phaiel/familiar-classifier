use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct Config {
    #[serde(default)]
    pub collection_name: String,
    
    #[serde(default)]
    pub confidence_threshold: f64,
    
    #[serde(default)]
    pub max_alternatives: i32,
    
    #[serde(default)]
    pub port: u16,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            collection_name: "pattern_index".to_string(),
            confidence_threshold: 0.5,
            max_alternatives: 3,
            port: 3000,
        }
    }
}

impl Config {
    pub fn from_env() -> Self {
        use std::env;
        Self {
            collection_name: env::var("COLLECTION_NAME").unwrap_or_else(|_| "pattern_index".to_string()),
            confidence_threshold: env::var("CONFIDENCE_THRESHOLD")
                .unwrap_or_else(|_| "0.5".to_string())
                .parse()
                .unwrap_or(0.5),
            max_alternatives: env::var("MAX_ALTERNATIVES")
                .unwrap_or_else(|_| "3".to_string())
                .parse()
                .unwrap_or(3),
            port: env::var("PORT")
                .unwrap_or_else(|_| "3000".to_string())
                .parse()
                .unwrap_or(3000),
        }
    }
}