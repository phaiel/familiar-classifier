//! Pattern Classification - Rust Hot Path (Simplified)
//! 
//! High-performance pattern classification service using:
//! - Qdrant vector database for fast similarity search
//! - Candle ML framework for native Rust embeddings
//! - Axum web framework for blazing fast API

pub mod generated;
pub mod config;
pub mod embeddings;
pub mod classifier;
pub mod service;

// Re-export main types for convenience
pub use config::Config;
pub use classifier::PatternClassifier;
pub use generated::*;
pub use service::ClassificationService; 