//! Pattern Classification - Rust Hot Path (Simplified)
//! 
//! High-performance pattern classification service using:
//! - Qdrant vector database for fast similarity search
//! - Candle ML framework for native Rust embeddings
//! - Axum web framework for blazing fast API

pub mod config;
pub mod embeddings;
pub mod classifier;
pub mod service;
pub mod stats;

pub mod generated {
    include!(concat!(env!("OUT_DIR"), "/generated.rs"));
}

pub use config::Config;
pub use classifier::HierarchicalClassifier;
pub use service::ClassificationService; 