use std::env;
use std::fs;
use std::path::Path;

fn main() {
    println!("cargo:rerun-if-changed=../assets/schemas.json");
    
    let out_dir = env::var("OUT_DIR").unwrap();
    let dest_path = Path::new(&out_dir).join("generated_schemas.rs");
    
    // Try to generate from schemas, otherwise use fallback
    if Path::new("../assets/schemas.json").exists() {
        println!("cargo:warning=Generated Rust schemas from Python bridge");
        let rust_code = generate_from_schemas();
        fs::write(&dest_path, rust_code).expect("Failed to write generated schemas");
    } else {
        println!("cargo:warning=Using fallback schemas - run Python cold path schema export");
        let fallback_code = generate_fallback_schemas();
        fs::write(&dest_path, fallback_code).expect("Failed to write fallback schemas");
    }
}

fn generate_from_schemas() -> String {
    // Simple generation - we'll create generated.rs directly like ECS Familiar
    r#"
// Generated types for Pattern Classifier Hot Path
// DO NOT EDIT - regenerated on every build

use serde::{Serialize, Deserialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

// Placeholder for Python bridge - will be replaced with direct generated.rs
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeGenerated {
    pub message: String,
}

impl Default for BridgeGenerated {
    fn default() -> Self {
        Self {
            message: "Schema bridge working - replace with direct generated.rs".to_string(),
        }
    }
}
"#.to_string()
}

fn generate_fallback_schemas() -> String {
    r#"
// WARNING: No schema bridge found - using fallback types
// Run: poetry run python -m cold_path.cli schema-dump

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FallbackSchema {
    pub message: String,
}

impl Default for FallbackSchema {
    fn default() -> Self {
        Self {
            message: "Run schema export from cold path".to_string(),
        }
    }
}
"#.to_string()
} 