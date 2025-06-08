use anyhow::{anyhow, Result};
use tracing::{info, warn};
use candle_core::{Device, Tensor, DType};
use candle_nn::VarBuilder;
use candle_transformers::models::bert::{BertModel, Config};
use tokenizers::Tokenizer;
use hf_hub::api::sync::Api;
use std::path::PathBuf;

/// Full Candle BERT embedding generator 
pub struct EmbeddingGenerator {
    model: BertModel,
    tokenizer: Tokenizer,
    device: Device,
    embedding_dim: usize,
}

impl EmbeddingGenerator {
    /// Create a new embedding generator using Candle + BERT
    pub async fn new(model_name: &str) -> Result<Self> {
        info!("🧠 Loading Candle BERT model: {}", model_name);
        
        let device = Device::Cpu;
        let api = Api::new()?;
        let repo = api.model("sentence-transformers/all-MiniLM-L6-v2".to_string());
        
        info!("📥 Downloading tokenizer...");
        let tokenizer_filename = repo.get("tokenizer.json")?;
        info!("📥 Downloading config...");
        let config_filename = repo.get("config.json")?;
        info!("📥 Downloading model weights...");
        let weights_filename = repo.get("model.safetensors")?;
        
        info!("🔧 Loading tokenizer...");
        let tokenizer = Tokenizer::from_file(tokenizer_filename)
            .map_err(|e| anyhow!("Failed to load tokenizer: {}", e))?;
        
        info!("🔧 Loading config...");
        let config_str = std::fs::read_to_string(config_filename)?;
        let config: Config = serde_json::from_str(&config_str)?;
        
        info!("🔧 Loading model weights...");
        let vb = unsafe { VarBuilder::from_mmaped_safetensors(&[weights_filename], DType::F32, &device)? };
        
        let model = BertModel::load(vb, &config)?;
        
        info!("✅ Candle BERT model loaded successfully");
        
        Ok(Self {
            model,
            tokenizer,
            device,
            embedding_dim: 384, // all-MiniLM-L6-v2 dimension
        })
    }
    
    /// Generate embedding for text using Candle BERT
    pub async fn encode(&self, text: &str) -> Result<Vec<f32>> {
        // Tokenize input
        let encoding = self.tokenizer
            .encode(text, true)
            .map_err(|e| anyhow!("Tokenization failed: {}", e))?;
        
        let tokens = encoding.get_ids();
        let token_ids = Tensor::new(tokens, &self.device)?;
        let token_type_ids = token_ids.zeros_like()?;
        
        // Create attention mask (all 1s for our tokens) as F32
        let attention_mask = Tensor::ones(token_ids.shape(), DType::F32, &self.device)?;
        
        // Add batch dimension
        let token_ids = token_ids.unsqueeze(0)?;
        let token_type_ids = token_type_ids.unsqueeze(0)?;
        let attention_mask = attention_mask.unsqueeze(0)?;
        
        // Forward pass through BERT
        let sequence_output = self.model.forward(&token_ids, &token_type_ids, Some(&attention_mask))?;
        
        // Mean pooling over sequence length (excluding padding)
        // Multiply by attention mask to zero out padding positions
        let attention_mask_expanded = attention_mask.unsqueeze(2)?;
        let masked_output = sequence_output.broadcast_mul(&attention_mask_expanded)?;
        
        // Sum over sequence length
        let sum_embeddings = masked_output.sum(1)?;
        
        // Get the sum of attention mask for normalization
        let sum_mask = attention_mask.sum(1)?;
        let sum_mask_expanded = sum_mask.unsqueeze(1)?;
        
        // Compute mean pooling
        let mean_embeddings = sum_embeddings.broadcast_div(&sum_mask_expanded)?;
        
        // Convert to Vec<f32>
        let embedding_vec = mean_embeddings.squeeze(0)?.to_vec1::<f32>()?;
        
        Ok(embedding_vec)
    }
    
    /// Get embedding dimension
    pub fn embedding_dim(&self) -> usize {
        self.embedding_dim
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_embedding_generation() {
        let generator = EmbeddingGenerator::new("all-MiniLM-L6-v2").await.unwrap();
        let embedding = generator.encode("test text").await.unwrap();
        
        assert_eq!(embedding.len(), 384);
        
        // Check that embedding has reasonable values
        let norm: f32 = embedding.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert!(norm > 0.0);
    }
    
    #[tokio::test]
    async fn test_embedding_semantic_similarity() {
        let generator = EmbeddingGenerator::new("all-MiniLM-L6-v2").await.unwrap();
        
        let embedding1 = generator.encode("The dog is playing in the park").await.unwrap();
        let embedding2 = generator.encode("A puppy is having fun outdoors").await.unwrap();
        let embedding3 = generator.encode("I am studying mathematics").await.unwrap();
        
        // Compute cosine similarities
        let sim_12 = cosine_similarity(&embedding1, &embedding2);
        let sim_13 = cosine_similarity(&embedding1, &embedding3);
        
        // Similar sentences should have higher similarity than dissimilar ones
        assert!(sim_12 > sim_13);
    }
}

fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    
    if norm_a == 0.0 || norm_b == 0.0 { 0.0 } else { dot_product / (norm_a * norm_b) }
} 