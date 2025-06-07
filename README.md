# Familiar Pattern Classifier

A **database-agnostic**, **lightning-fast** pattern classification system built following the ECS Familiar architecture. Features a Python cold path for schema management and pattern indexing, with a Rust hot path for real-time classification.

## 🚀 Features

- ✅ **Database Agnostic**: Switch between in-memory, Qdrant, or other vector stores
- ⚡ **Lightning Fast**: 0.0ms classification with in-memory vector store
- 🧠 **Self-Contained**: Zero external dependencies for core functionality
- 🔗 **Type-Safe**: Python → Rust schema bridge with Pydantic validation
- 📊 **Real-Time**: REST API for instant pattern classification
- 🎯 **ECS Familiar**: Follows established architecture patterns

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│   Cold Path (Python)│    │   Hot Path (Rust)   │
│                     │    │                     │
│ • Pattern Loading   │───▶│ • Vector Store      │
│ • Schema Management │    │ • Classification    │
│ • Embedding Gen     │    │ • REST API          │
│ • Index Building    │    │ • Real-time Perf    │
└─────────────────────┘    └─────────────────────┘
```

### Cold Path (Python)
- **Pattern management** with YAML definitions
- **Schema validation** using Pydantic
- **Embedding generation** with sentence transformers
- **Database-agnostic indexing** (in-memory, Qdrant, etc.)

### Hot Path (Rust)
- **In-memory vector store** for lightning performance  
- **REST API** with Axum web framework
- **Real-time classification** with cosine similarity
- **Type-safe schemas** generated from Python

## 🛠️ Installation

### Prerequisites
- **Python 3.11+** with Poetry
- **Rust 1.70+** with Cargo
- **macOS/Linux** (Windows untested)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/familiar-classifier.git
cd familiar-classifier

# Install Python dependencies
poetry install

# Build Rust hot path
cd hot_path
cargo build --release
```

## 🔧 Usage

### 1. Cold Path - Pattern Management

```bash
# Validate pattern definitions
poetry run python -m cold_path.cli patterns-validate

# Generate schemas for hot path
poetry run python -m cold_path.cli schema-dump

# Build vector index (database agnostic)
poetry run python -m cold_path.cli index-build --vector-store in_memory

# Use Qdrant instead
poetry run python -m cold_path.cli index-build --vector-store qdrant --port 6333
```

### 2. Hot Path - Real-time Classification

```bash
# Start the classification service
cd hot_path
cargo run

# Service runs on http://localhost:3000
```

### 3. API Usage

```bash
# Health check
curl http://localhost:3000/health

# Get service status
curl http://localhost:3000/status

# Classify text
curl -X POST http://localhost:3000/classify \
  -H "Content-Type: application/json" \
  -d '{
    "weaveUnit": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "text": "my child is playing at the park this afternoon"
    },
    "confidenceThreshold": 0.1
  }'

# Reload patterns
curl -X POST http://localhost:3000/reload-patterns \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 📊 Performance

- **Classification**: 0.0ms average processing time
- **Vector Store**: In-memory for maximum speed
- **Startup**: ~3 seconds with pattern loading
- **Throughput**: Limited by network, not computation

## 🎯 Pattern Definitions

Patterns are defined in YAML files under `cold_path/patterns/`:

```yaml
id: "child_development/play/outdoor/park/afternoon"
description: "Afternoon play session at the park"
domain: "child_development"
category: "play"
mixins: [TIME, LOCATION]
sample_texts:
  - "Spent the afternoon playing at the park."
  - "Had fun on the swings and slides this afternoon."
  - "Great afternoon of outdoor play at the local park."
metadata:
  age_range: "2-12 years"
  typical_duration: "60-180 minutes"
  weather_dependent: true
```

## 🗂️ Project Structure

```
familiar-classifier/
├── cold_path/           # Python pattern management
│   ├── patterns/        # YAML pattern definitions
│   ├── schemas.py       # Pydantic models
│   ├── cli.py          # Command-line interface
│   └── vector_stores.py # Database abstraction
├── hot_path/           # Rust classification service
│   ├── src/
│   │   ├── main.rs     # Web server
│   │   ├── classifier.rs # Pattern classifier
│   │   └── generated.rs # Auto-generated schemas
│   └── Cargo.toml      # Rust dependencies
├── assets/             # Generated data files
└── README.md
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | Service statistics |
| `/classify` | POST | Classify text patterns |
| `/reload-patterns` | POST | Reload pattern index |

## 🧪 Example Response

```json
{
  "requestId": "f7f11219-9150-48d1-ba93-5e721b06bc50",
  "matchResult": {
    "patternId": "child_development/play/outdoor/park/afternoon",
    "confidence": 0.85,
    "alternatives": [],
    "metadata": {
      "domain": "child_development",
      "description": "Afternoon play session at the park"
    }
  },
  "alternatives": [
    {
      "patternId": "child_development/sleep/nap/crib/early_am", 
      "confidence": 0.12
    }
  ],
  "processingTimeMs": 0.0,
  "status": "success"
}
```

## 🎛️ Configuration

### Vector Store Types

- **`in_memory`**: Maximum performance, ephemeral storage
- **`qdrant`**: Persistent vector database, requires Qdrant server

### Environment Variables

```bash
# Hot path configuration
COLLECTION_NAME=pattern_index
CONFIDENCE_THRESHOLD=0.5
MAX_ALTERNATIVES=3
```

## 🚧 Development

### Adding New Patterns

1. Create YAML file in `cold_path/patterns/`
2. Run `poetry run python -m cold_path.cli patterns-validate`
3. Build index: `poetry run python -m cold_path.cli index-build`
4. Reload in hot path: `curl -X POST http://localhost:3000/reload-patterns`

### Testing

```bash
# Python tests
poetry run pytest

# Rust tests  
cd hot_path
cargo test
```

## 🏛️ Architecture Philosophy

This project follows the **ECS Familiar** architecture:

- **Cold Path**: Schema management, validation, data preparation
- **Hot Path**: Real-time performance, minimal dependencies
- **Type Safety**: Shared schemas between Python and Rust
- **Database Agnostic**: Pluggable storage backends
- **Self-Contained**: Minimal external dependencies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built following the **ECS Familiar** architecture patterns
- Inspired by modern vector search and ML classification systems
- Uses Rust for performance-critical hot path operations