# Familiar Pattern Classifier

A **database-agnostic**, **lightning-fast** pattern classification system built following the ECS Familiar architecture. Features a Python cold path for schema management and pattern indexing, with a Rust hot path for real-time classification, plus a modern web UI for pattern creation and testing.

## 🚀 Features

- ✅ **Database Agnostic**: Switch between in-memory, Qdrant, or other vector stores
- ⚡ **Lightning Fast**: 0.0ms classification with in-memory vector store
- 🧠 **Self-Contained**: Zero external dependencies for core functionality
- 🔗 **Type-Safe**: Python → Rust schema bridge with Pydantic validation
- 📊 **Real-Time**: REST API for instant pattern classification
- 🎯 **ECS Familiar**: Follows established architecture patterns
- 🎨 **Modern Web UI**: Streamlit interface for pattern creation and chat-based testing
- 🏗️ **6-Level Hierarchy**: Domain/Area/Topic/Theme/Focus/Form with temporal marker support
- 🕒 **Temporal Analysis**: Automatic collision detection and resolution recommendations

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Web UI (Streamlit)│    │   Cold Path (Python)│    │   Hot Path (Rust)   │
│                     │    │                     │    │                     │
│ • Pattern Creation  │───▶│ • Pattern Loading   │───▶│ • Vector Store      │
│ • Classification UI │    │ • Schema Management │    │ • Classification    │
│ • System Monitoring │    │ • Embedding Gen     │    │ • REST API          │
│ • Chat Interface    │────┼─▶ Index Building    │    │ • Real-time Perf    │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
       │                                                        ▲
       │                         HTTP/JSON                      │
       └────────────────────────────────────────────────────────┘
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

### Web UI (Streamlit)
- **Pattern Creation Interface** with 6-level hierarchy builder
- **Classification Chat** for interactive testing
- **System Monitoring** with real-time status
- **Temporal Analysis** for pattern collision detection

## ⚡ Quick Start

```bash
# One-command startup (everything included)
./start_system.sh
```

Then visit **http://localhost:8501** for the web UI!

## 🛠️ Installation

### Prerequisites
- **Python 3.11+** 
- **Rust 1.70+** with Cargo
- **macOS/Linux** (Windows untested)

### Manual Setup

```bash
# Clone the repository
git clone https://github.com/phaiel/familiar-classifier.git
cd familiar-classifier

# Install UI dependencies
pip install -r ui/requirements.txt

# Build Rust hot path
cd hot_path
cargo build --release
```

## 🔧 Usage

### 1. Web UI - Complete Interface

```bash
# Start everything with one command
./start_system.sh

# Or manually:
# 1. Start hot path: cd hot_path && cargo run
# 2. Start UI: python ui/run_ui.py
```

Access the web interface at **http://localhost:8501**:
- 🎨 **Pattern Creation**: Build patterns with 6-level hierarchy
- 💬 **Classification Chat**: Test patterns interactively
- 🔍 **System Monitoring**: Real-time service status

### 2. CLI Tools - Advanced Operations

```bash
# Validate pattern definitions
python -m cold_path.cli patterns-validate

# Analyze temporal patterns
python -m cold_path.cli temporal-analysis

# Generate schemas for hot path
python -m cold_path.cli schema-dump

# Build vector index (database agnostic)
python -m cold_path.cli index-build --vector-store in_memory
```

### 3. Hot Path API - Direct Integration

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
├── ui/                 # Streamlit web interface
│   ├── app.py          # Main web application
│   ├── run_ui.py       # UI launcher script
│   ├── requirements.txt # UI dependencies
│   └── README.md       # UI documentation
├── cold_path/          # Python pattern management
│   ├── patterns/       # YAML pattern definitions
│   ├── schemas.py      # Pydantic models (6-level hierarchy)
│   ├── cli.py          # Command-line interface
│   ├── pattern_loader.py # Pattern loading utilities
│   └── vector_stores.py # Database abstraction
├── hot_path/           # Rust classification service
│   ├── src/
│   │   ├── main.rs     # Web server
│   │   ├── classifier.rs # Pattern classifier
│   │   └── generated.rs # Auto-generated schemas
│   └── Cargo.toml      # Rust dependencies
├── test_patterns/      # Test pattern examples
├── assets/             # Generated data files
├── start_system.sh     # One-command startup script
├── HIERARCHY_ANALYSIS.md # Temporal analysis documentation
└── README.md
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | Service statistics |
| `/classify` | POST | Classify text patterns |
| `/reload-patterns` | POST | Reload pattern index |

## 🎭 Demo: 6-Level Hierarchy with Temporal Markers

```yaml
# Example pattern with full 6-level hierarchy
id: "child_development/sleep/nap/crib/early_am/single_entry"
#    └─ Domain ──┘ └─ Area ─┘ └─Topic─┘ └Theme┘ └─Focus──┘ └─ Form ──┘
#    Conceptual    Life zone  Function  Behavior Temporal   Pattern
#    group         type       group     cluster  context    variant

description: "Early morning crib nap - single entry pattern"
mixins: ["time", "location", "development"]
sample_texts:
  - "She went down for her early morning nap at 7:30am without fuss"
  - "Early AM crib nap successful - 7am to 8:30am"
```

**Why temporal markers matter:**
- `early_am` nap: Peaceful, easy transition
- `afternoon` nap: Often requires multiple attempts
- Without temporal markers: **Classification collision!**

## 🧪 Example Response

```json
{
  "requestId": "f7f11219-9150-48d1-ba93-5e721b06bc50",
  "matchResult": {
    "patternId": "child_development/sleep/nap/crib/early_am/single_entry",
    "confidence": 0.92,
    "alternatives": [],
    "metadata": {
      "domain": "child_development",
      "description": "Early morning crib nap - single entry pattern",
      "hierarchy_depth": 6,
      "has_temporal": true
    }
  },
  "alternatives": [
    {
      "patternId": "child_development/sleep/nap/crib/afternoon/recurring", 
      "confidence": 0.15
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