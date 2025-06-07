use anyhow::{anyhow, Result};
use std::sync::Arc;
use tracing::{info, warn, error};
use std::collections::HashMap;
use serde_json::{self, Value};
use std::sync::RwLock;

use crate::config::Config;
use crate::embeddings::EmbeddingGenerator;
use crate::generated::*;

// Simple in-memory vector store - embedded directly to avoid import issues
#[derive(Debug, Clone)]
struct VectorPoint {
    pub id: String,
    pub vector: Vec<f32>,
    pub payload: HashMap<String, Value>,
    pub score: Option<f32>,
}

#[derive(Debug, Clone)]
struct VectorStore {
    points: Arc<RwLock<HashMap<String, VectorPoint>>>,
    next_id: Arc<RwLock<u64>>,
}

impl VectorStore {
    fn new() -> Self {
        Self {
            points: Arc::new(RwLock::new(HashMap::new())),
            next_id: Arc::new(RwLock::new(1)),
        }
    }

    fn add_point(&self, id: Option<String>, vector: Vec<f32>, payload: HashMap<String, Value>) -> Result<String> {
        let point_id = match id {
            Some(id) => id,
            None => {
                let mut next_id = self.next_id.write().map_err(|_| anyhow!("Lock failed"))?;
                let id = format!("point_{}", *next_id);
                *next_id += 1;
                id
            }
        };

        let point = VectorPoint {
            id: point_id.clone(),
            vector,
            payload,
            score: None,
        };

        let mut points = self.points.write().map_err(|_| anyhow!("Lock failed"))?;
        points.insert(point_id.clone(), point);
        Ok(point_id)
    }

    fn search(&self, query_vector: Vec<f32>, limit: usize, score_threshold: Option<f32>, filter: Option<HashMap<String, Value>>) -> Result<Vec<VectorPoint>> {
        let points = self.points.read().map_err(|_| anyhow!("Lock failed"))?;
        let mut scored_points = Vec::new();

        for point in points.values() {
            // Apply filter if specified
            if let Some(ref filter_criteria) = filter {
                let mut matches_filter = true;
                for (key, expected_value) in filter_criteria {
                    match point.payload.get(key) {
                        Some(actual_value) if actual_value == expected_value => {}
                        _ => {
                            matches_filter = false;
                            break;
                        }
                    }
                }
                if !matches_filter {
                    continue;
                }
            }

            // Calculate cosine similarity
            let similarity = cosine_similarity(&query_vector, &point.vector)?;
            
            // Apply score threshold
            if let Some(threshold) = score_threshold {
                if similarity < threshold {
                    continue;
                }
            }

            let mut scored_point = point.clone();
            scored_point.score = Some(similarity);
            scored_points.push(scored_point);
        }

        // Sort by score (highest first)
        scored_points.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
        scored_points.truncate(limit);
        Ok(scored_points)
    }

    fn count(&self) -> Result<usize> {
        let points = self.points.read().map_err(|_| anyhow!("Lock failed"))?;
        Ok(points.len())
    }

    fn stats(&self) -> Result<HashMap<String, Value>> {
        let points = self.points.read().map_err(|_| anyhow!("Lock failed"))?;
        let mut domain_counts: HashMap<String, u32> = HashMap::new();
        
        for point in points.values() {
            if let Some(domain) = point.payload.get("domain").and_then(|v| v.as_str()) {
                *domain_counts.entry(domain.to_string()).or_insert(0) += 1;
            }
        }

        let mut stats = HashMap::new();
        stats.insert("total_points".to_string(), Value::Number(points.len().into()));
        stats.insert("domains".to_string(), Value::Object(
            domain_counts.into_iter()
                .map(|(k, v)| (k, Value::Number(v.into())))
                .collect()
        ));
        stats.insert("storage_type".to_string(), Value::String("in_memory".to_string()));
        Ok(stats)
    }
}

fn cosine_similarity(a: &[f32], b: &[f32]) -> Result<f32> {
    if a.len() != b.len() {
        return Err(anyhow!("Vector dimensions don't match: {} vs {}", a.len(), b.len()));
    }

    let mut dot_product = 0.0;
    let mut norm_a = 0.0;
    let mut norm_b = 0.0;

    for i in 0..a.len() {
        dot_product += a[i] * b[i];
        norm_a += a[i] * a[i];
        norm_b += b[i] * b[i];
    }

    if norm_a == 0.0 || norm_b == 0.0 {
        return Ok(0.0);
    }

    Ok(dot_product / (norm_a.sqrt() * norm_b.sqrt()))
}

/// Simple in-memory pattern classifier - no external dependencies!
pub struct PatternClassifier {
    vector_store: VectorStore,
    embedding_generator: Arc<EmbeddingGenerator>,
    config: Config,
}

impl PatternClassifier {
    /// Create a new in-memory pattern classifier
    pub async fn new(config: Config) -> Result<Self> {
        info!("🔥 Initializing In-Memory Pattern Classifier");
        
        // Initialize vector store
        let vector_store = VectorStore::new();
        
        // Initialize embedding generator
        let embedding_generator = Arc::new(
            EmbeddingGenerator::new("all-MiniLM-L6-v2").await?
        );
        
        let classifier = Self {
            vector_store,
            embedding_generator,
            config,
        };
        
        // Try to load patterns from the cold path export
        if let Err(e) = classifier.load_patterns_from_file("assets/patterns_with_embeddings.json").await {
            warn!("⚠️  Could not load patterns from file: {}", e);
            info!("🔄 Starting with empty vector store - patterns can be loaded later");
        }
        
        info!("✅ In-memory pattern classifier initialized");
        
        Ok(classifier)
    }
    
    /// Load patterns from JSON file (generated by cold path)
    pub async fn load_patterns_from_file(&self, file_path: &str) -> Result<usize> {
        use std::fs;
        use serde_json::Value;
        
        info!("📂 Loading patterns from: {}", file_path);
        
        // Read and parse JSON file
        let file_content = fs::read_to_string(file_path)
            .map_err(|e| anyhow!("Failed to read file {}: {}", file_path, e))?;
        
        let patterns: Vec<Value> = serde_json::from_str(&file_content)
            .map_err(|e| anyhow!("Failed to parse JSON: {}", e))?;
        
        info!("📋 Found {} patterns in file", patterns.len());
        
        let mut loaded_count = 0;
        
        for pattern in patterns {
            // Extract pattern data
            let id = pattern.get("id")
                .and_then(|v| v.as_str())
                .ok_or_else(|| anyhow!("Pattern missing 'id' field"))?;
            
            let description = pattern.get("description")
                .and_then(|v| v.as_str())
                .unwrap_or("No description");
            
            let domain = pattern.get("domain")
                .and_then(|v| v.as_str())
                .map(|s| s.to_string());
            
            let sample_texts = pattern.get("sample_texts")
                .and_then(|v| v.as_array())
                .map(|arr| {
                    arr.iter()
                        .filter_map(|v| v.as_str())
                        .map(|s| s.to_string())
                        .collect::<Vec<String>>()
                })
                .unwrap_or_default();
            
            let metadata = pattern.get("metadata")
                .and_then(|v| v.as_object())
                .cloned()
                .unwrap_or_default()
                .into_iter()
                .map(|(k, v)| (k, v))
                .collect::<HashMap<String, Value>>();
            
            // Get the pre-computed embedding
            let embedding = pattern.get("embedding")
                .and_then(|v| v.as_array())
                .ok_or_else(|| anyhow!("Pattern '{}' missing embedding", id))?
                .iter()
                .map(|v| v.as_f64().unwrap_or(0.0) as f32)
                .collect::<Vec<f32>>();
            
            if embedding.len() != 384 {
                warn!("⚠️  Pattern '{}' has embedding dimension {} (expected 384)", id, embedding.len());
                continue;
            }
            
            // Add to vector store using the pre-computed embedding
            let mut payload = HashMap::new();
            payload.insert("pattern_id".to_string(), Value::String(id.to_string()));
            payload.insert("description".to_string(), Value::String(description.to_string()));
            
            if let Some(ref domain) = domain {
                payload.insert("domain".to_string(), Value::String(domain.clone()));
            }
            
            // Add custom metadata
            for (key, value) in &metadata {
                payload.insert(key.clone(), value.clone());
            }
            
            // Add sample texts as a combined field (for reference)
            if !sample_texts.is_empty() {
                payload.insert("sample_texts".to_string(), Value::Array(
                    sample_texts.iter().map(|s| Value::String(s.clone())).collect()
                ));
                payload.insert("primary_text".to_string(), Value::String(sample_texts[0].clone()));
            }
            
            // Add the pattern with pre-computed embedding
            let point_id = id.replace("/", "_");
            self.vector_store.add_point(Some(point_id), embedding, payload)?;
            
            loaded_count += 1;
        }
        
        info!("✅ Successfully loaded {} patterns into vector store", loaded_count);
        Ok(loaded_count)
    }
    
    /// Add patterns to the vector store (called from cold path)
    pub async fn add_pattern(
        &self,
        pattern_id: String,
        description: String,
        sample_texts: Vec<String>,
        domain: Option<String>,
        metadata: HashMap<String, Value>
    ) -> Result<()> {
        // Generate embeddings for all sample texts
        for (i, text) in sample_texts.iter().enumerate() {
            let embedding = self.embedding_generator.encode(text).await?;
            
            let point_id = format!("{}_{}", pattern_id.replace("/", "_"), i);
            
            let mut payload = HashMap::new();
            payload.insert("pattern_id".to_string(), Value::String(pattern_id.clone()));
            payload.insert("description".to_string(), Value::String(description.clone()));
            payload.insert("sample_text".to_string(), Value::String(text.clone()));
            payload.insert("text_index".to_string(), Value::Number((i as u64).into()));
            
            if let Some(ref domain) = domain {
                payload.insert("domain".to_string(), Value::String(domain.clone()));
            }
            
            // Add custom metadata
            for (key, value) in &metadata {
                payload.insert(key.clone(), value.clone());
            }
            
            self.vector_store.add_point(Some(point_id), embedding, payload)?;
        }
        
        info!("📝 Added pattern '{}' with {} sample texts", pattern_id, sample_texts.len());
        Ok(())
    }
    
    /// Classify text using in-memory vector search
    pub async fn classify(
        &self, 
        text: &str,
        confidence_threshold: f64,
        max_alternatives: usize,
        filter_by_domain: Option<&str>,
    ) -> Result<(Option<PatternMatch>, Vec<PatternMatch>)> {
        
        // Generate embedding
        let embedding = self.embedding_generator.encode(text).await?;
        
        // Build filter if domain specified
        let filter = if let Some(domain) = filter_by_domain {
            let mut filter_map = HashMap::new();
            filter_map.insert("domain".to_string(), Value::String(domain.to_string()));
            Some(filter_map)
        } else {
            None
        };
        
        // Perform search
        let search_results = self.vector_store.search(
            embedding,
            max_alternatives + 5, // Get a few extra to account for duplicates
            Some(confidence_threshold as f32),
            filter,
        )?;
        
        // Process results - deduplicate by pattern_id and keep best score
        let mut pattern_scores: HashMap<String, (f64, VectorPoint)> = HashMap::new();
        
        for point in search_results {
            let pattern_id = point.payload.get("pattern_id")
                .and_then(|v| v.as_str())
                .unwrap_or("unknown")
                .to_string();
            
            let score = point.score.unwrap_or(0.0) as f64;
            
            // Keep the best score for each pattern
            match pattern_scores.get(&pattern_id) {
                Some((existing_score, _)) if score <= *existing_score => {
                    // Skip this one, we have a better score
                }
                _ => {
                    pattern_scores.insert(pattern_id, (score, point));
                }
            }
        }
        
        // Convert to PatternMatch and sort by score
        let mut matches: Vec<(f64, PatternMatch)> = pattern_scores
            .into_iter()
            .map(|(pattern_id, (score, point))| {
                let mut metadata = HashMap::new();
                
                // Extract metadata
                if let Some(domain) = point.payload.get("domain").and_then(|v| v.as_str()) {
                    metadata.insert("domain".to_string(), Value::String(domain.to_string()));
                }
                if let Some(desc) = point.payload.get("description").and_then(|v| v.as_str()) {
                    metadata.insert("description".to_string(), Value::String(desc.to_string()));
                }
                if let Some(sample) = point.payload.get("sample_text").and_then(|v| v.as_str()) {
                    metadata.insert("sample_text".to_string(), Value::String(sample.to_string()));
                }
                
                let pattern_match = PatternMatch {
                    pattern_id,
                    confidence: score,
                    alternatives: Vec::new(),
                    embedding_vector: None,
                    metadata,
                };
                
                (score, pattern_match)
            })
            .collect();
        
        // Sort by score (highest first)
        matches.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
        
        // Extract just the PatternMatch objects
        let mut pattern_matches: Vec<PatternMatch> = matches.into_iter().map(|(_, pm)| pm).collect();
        
        // Return primary match and alternatives
        let primary = if pattern_matches.is_empty() {
            None
        } else {
            Some(pattern_matches.remove(0))
        };
        
        let alternatives = pattern_matches.into_iter().take(max_alternatives).collect();
        
        Ok((primary, alternatives))
    }
    
    /// Health check for in-memory vector store
    pub async fn health_check(&self) -> Result<()> {
        let count = self.vector_store.count()?;
        info!("📊 In-memory vector store healthy - {} patterns loaded", count);
        Ok(())
    }
    
    /// Get database statistics
    pub async fn get_stats(&self) -> Result<Value> {
        let stats = self.vector_store.stats()?;
        let count = self.vector_store.count()?;
        
        let mut extended_stats = stats;
        extended_stats.insert("total_points".to_string(), Value::Number(count.into()));
        extended_stats.insert("classifier_type".to_string(), Value::String("in_memory".to_string()));
        
        Ok(serde_json::to_value(extended_stats)?)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_classification_request() {
        let request = ClassificationRequest::new("test text".to_string());
        assert_eq!(request.text, "test text");
        assert!(request.confidence_threshold.is_none());
    }
} 