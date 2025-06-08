use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use anyhow::{anyhow, Result};
use tracing::{info, warn, debug};
use serde_json::Value;

use crate::embeddings::EmbeddingGenerator;
use crate::config::Config;
use crate::generated::PatternMatch;

#[derive(Debug, Clone)]
struct VectorPoint {
    pub vector: Vec<f32>,
    pub payload: HashMap<String, Value>,
}

#[derive(Debug, Clone)]
struct LevelSchema {
    pub id: String,
    pub level: String,
    pub parent_id: Option<String>,
    pub embedding: Vec<f32>,
}

/// A lean, mean, hierarchical classifier.
/// This struct holds both the level schemas for navigation and the final pattern vectors.
pub struct HierarchicalClassifier {
    patterns: Arc<RwLock<HashMap<String, VectorPoint>>>,
    level_schemas: Arc<RwLock<Vec<LevelSchema>>>,
    embedding_generator: Arc<EmbeddingGenerator>,
}

impl HierarchicalClassifier {
    pub async fn new(_config: Config) -> Result<Self> {
        info!("🔥 Initializing Hierarchical Classifier");
        
        let classifier = Self {
            patterns: Arc::new(RwLock::new(HashMap::new())),
            level_schemas: Arc::new(RwLock::new(Vec::new())),
            embedding_generator: Arc::new(EmbeddingGenerator::new("all-MiniLM-L6-v2").await?),
        };
        
        if let Err(e) = classifier.load_patterns_from_file("assets/patterns_with_embeddings.json").await {
            warn!("⚠️  Could not load patterns: {}", e);
        }
        if let Err(e) = classifier.load_level_schemas("assets/level_schemas_with_embeddings.json").await {
            warn!("⚠️  Could not load level schemas: {}", e);
        }
        
        info!("✅ Hierarchical Classifier initialized");
        Ok(classifier)
    }
    
    pub async fn load_patterns_from_file(&self, file_path: &str) -> Result<usize> {
        info!("📂 Loading patterns from: {}", file_path);
        let pattern_data: Vec<Value> = serde_json::from_str(&std::fs::read_to_string(file_path)?)?;
        
        let mut patterns = self.patterns.write().map_err(|_| anyhow!("Lock failed"))?;
        patterns.clear();
        
        for pattern in pattern_data {
            let id = pattern.get("id").and_then(|v| v.as_str()).ok_or_else(|| anyhow!("Missing pattern id"))?;
            let embedding: Vec<f32> = pattern.get("embedding").and_then(|v| v.as_array())
                .ok_or_else(|| anyhow!("Missing embedding"))?
                .iter().map(|v| v.as_f64().unwrap_or(0.0) as f32).collect();
            
            if embedding.len() != 384 { continue; }
            
            let mut payload = HashMap::new();
            payload.insert("pattern_id".to_string(), Value::String(id.to_string()));
            if let Some(desc) = pattern.get("description").and_then(|v| v.as_str()) {
                payload.insert("description".to_string(), Value::String(desc.to_string()));
            }
            if let Some(domain) = pattern.get("domain").and_then(|v| v.as_str()) {
                payload.insert("domain".to_string(), Value::String(domain.to_string()));
            }
            
            patterns.insert(id.replace("/", "_"), VectorPoint { vector: embedding, payload });
        }
        
        let count = patterns.len();
        info!("✅ Loaded {} patterns", count);
        Ok(count)
    }
    
    pub async fn load_level_schemas(&self, file_path: &str) -> Result<usize> {
        info!("📂 Loading level schemas from: {}", file_path);
        let level_data: Vec<Value> = serde_json::from_str(&std::fs::read_to_string(file_path)?)?;
        
        let mut schemas = self.level_schemas.write().map_err(|_| anyhow!("Lock failed"))?;
        schemas.clear();
        
        for item in level_data {
            let id = item.get("id").and_then(|v| v.as_str()).ok_or_else(|| anyhow!("Missing id"))?;
            let level = item.get("level").and_then(|v| v.as_str()).unwrap_or("unknown");
            let parent_id = item.get("parent_id").and_then(|v| v.as_str()).map(|s| s.to_string());
            let embedding: Vec<f32> = item.get("embedding").and_then(|v| v.as_array())
                .ok_or_else(|| anyhow!("Missing embedding"))?
                .iter().map(|v| v.as_f64().unwrap_or(0.0) as f32).collect();
            
            if embedding.len() != 384 { continue; }
            
            schemas.push(LevelSchema { id: id.to_string(), level: level.to_string(), parent_id, embedding });
        }
        
        let count = schemas.len();
        info!("✅ Loaded {} level schemas", count);
        Ok(count)
    }
    
    pub async fn classify(&self, text: &str, confidence_threshold: f64, max_alternatives: usize) -> Result<(Option<PatternMatch>, Vec<PatternMatch>, Vec<String>)> {
        let mut steps = Vec::new();
        let embedding = self.embedding_generator.encode(text).await?;

        // Step 1 & 2 & 3: Find the best hierarchical path (Domain -> Area -> Topic)
        let domain_candidates = self.classify_at_level(&embedding, "domain", None).await?;
        if domain_candidates.is_empty() { return Ok((None, vec![], vec!["No domain matches found.".into()])); }
        let (best_domain, domain_conf) = &domain_candidates[0];
        steps.push(format!("✅ Domain: {} ({:.1}%)", best_domain, domain_conf * 100.0));

        let area_candidates = self.classify_at_level(&embedding, "area", Some(best_domain)).await?;
        if area_candidates.is_empty() { return Ok((None, vec![], steps)); }
        let (best_area, area_conf) = &area_candidates[0];
        steps.push(format!("✅ Area: {} ({:.1}%)", best_area, area_conf * 100.0));

        let topic_candidates = self.classify_at_level(&embedding, "topic", Some(best_area)).await?;
        if topic_candidates.is_empty() { return Ok((None, vec![], steps)); }
        let (best_topic, topic_conf) = &topic_candidates[0];
        steps.push(format!("✅ Topic: {} ({:.1}%)", best_topic, topic_conf * 100.0));
        
        // Step 4: Run vector search ONLY within the identified subspace
        let pattern_prefix = format!("{}/{}/{}", best_domain, best_area, best_topic);
        let final_candidates = self.find_patterns_in_subspace(&embedding, &pattern_prefix, confidence_threshold, max_alternatives).await?;

        if final_candidates.is_empty() {
            steps.push(format!("❌ No final pattern matches found under '{}' with threshold > {:.1}%", pattern_prefix, confidence_threshold * 100.0));
            return Ok((None, Vec::new(), steps));
        }

        // Step 5: Apply confidence weighting to the results from the correct subspace
        let mut results: Vec<PatternMatch> = final_candidates.into_iter().map(|(pattern_id, pattern_similarity, _point)| {
            // New confidence: pattern's cosine score blended with the confidence of the hierarchical path.
            let final_confidence = pattern_similarity * (domain_conf * 0.4 + area_conf * 0.3 + topic_conf * 0.3);
            PatternMatch {
                pattern_id,
                confidence: final_confidence,
                ..Default::default()
            }
        }).collect();
        
        results.sort_by(|a, b| b.confidence.partial_cmp(&a.confidence).unwrap_or(std::cmp::Ordering::Equal));
        
        let primary = results.remove(0);
        steps.push(format!("🎯 Final: {} ({:.1}%)", primary.pattern_id, primary.confidence * 100.0));

        Ok((Some(primary), results, steps))
    }
    
    async fn classify_at_level(&self, embedding: &[f32], level: &str, parent_filter: Option<&str>) -> Result<Vec<(String, f64)>> {
        let schemas = self.level_schemas.read().map_err(|_| anyhow!("Lock failed"))?;
        let mut scores: Vec<(String, f64)> = schemas.iter()
            .filter(|s| s.level == level)
            .filter(|s| parent_filter.map_or(true, |p| s.parent_id.as_deref() == Some(p)))
            .map(|s| {
                let similarity = cosine_similarity(embedding, &s.embedding) as f64;
                (s.id.clone(), similarity)
            })
            .collect();
        
        scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        Ok(scores)
    }
    
    async fn find_patterns_in_subspace(&self, embedding: &[f32], prefix: &str, threshold: f64, limit: usize) -> Result<Vec<(String, f64, VectorPoint)>> {
        let patterns = self.patterns.read().map_err(|_| anyhow!("Lock failed"))?;
        let replaced_prefix = prefix.replace("/", "_");
        
        info!(target: "classifier", "Searching for patterns with prefix: '{}', threshold: {}", prefix, threshold);

        let mut results: Vec<(String, f64, VectorPoint)> = patterns.iter()
            .filter(|(id, _)| id.starts_with(&replaced_prefix))
            .filter_map(|(_, point)| {
                let similarity = cosine_similarity(embedding, &point.vector) as f64;
                
                let pattern_id = point.payload.get("pattern_id").and_then(|v| v.as_str()).unwrap_or("unknown");
                debug!(target: "classifier", "Pattern: {}, Similarity: {:.4}", pattern_id, similarity);

                if similarity >= threshold {
                    Some((pattern_id.to_string(), similarity, point.clone()))
                } else { 
                    None 
                }
            })
            .collect();
            
        info!(target: "classifier", "Found {} patterns matching prefix '{}' above threshold", results.len(), prefix);

        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        results.truncate(limit);
        Ok(results)
    }

    pub async fn health_check(&self) -> Result<()> {
        let count = self.patterns.read().map_err(|_| anyhow!("Lock failed"))?.len();
        info!("📊 Classifier healthy - {} patterns loaded", count);
        Ok(())
    }
}

fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() { return 0.0; }
    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm_a == 0.0 || norm_b == 0.0 { 0.0 } else { dot_product / (norm_a * norm_b) }
} 