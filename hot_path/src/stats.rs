use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct StatsTracker {
    requests_processed: u64,
    total_processing_time: Duration,
    errors: u64,
}

impl StatsTracker {
    pub fn new() -> Self {
        Self {
            requests_processed: 0,
            total_processing_time: Duration::new(0, 0),
            errors: 0,
        }
    }

    pub fn log_request(&mut self, processing_time: f64) {
        self.requests_processed += 1;
        self.total_processing_time += Duration::from_secs_f64(processing_time / 1000.0);
    }

    pub fn log_error(&mut self) {
        self.errors += 1;
    }

    pub fn get_summary(&self) -> serde_json::Value {
        let avg_time = if self.requests_processed > 0 {
            self.total_processing_time.as_millis() as f64 / self.requests_processed as f64
        } else {
            0.0
        };
        
        serde_json::json!({
            "requests_processed": self.requests_processed,
            "total_processing_time_ms": self.total_processing_time.as_millis(),
            "average_processing_time_ms": avg_time,
            "errors": self.errors,
            "error_rate": if self.requests_processed > 0 { self.errors as f64 / self.requests_processed as f64 } else { 0.0 }
        })
    }
} 