# 🧠 Familiar Classifier UI

Modern web interface for creating patterns and testing classification with the Familiar Classifier system.

## ✨ Features

### 🎨 Pattern Creation
- **6-Level Hierarchy Builder**: Guided creation of Domain/Area/Topic/Theme/Focus/Form patterns
- **Real-time Validation**: Instant schema validation and preview
- **Auto-generated IDs**: Automatic pattern ID generation from hierarchy
- **Temporal Marker Support**: Special handling for time-based patterns
- **Mixin Selection**: Choose from available pattern mixins
- **YAML Export**: Direct saving to pattern directory

### 💬 Classification Chat
- **Real-time Classification**: Send text and get instant pattern matches
- **Confidence Scoring**: See confidence levels and alternatives
- **Chat History**: Persistent session history
- **Performance Metrics**: Processing time and system status
- **Hot Path Integration**: Direct communication with Rust service

### 🔍 System Monitoring
- **Hot Path Status**: Real-time service health checks
- **Pattern Statistics**: Live metrics on pattern collection
- **Quick Actions**: Reload patterns, health checks
- **Error Handling**: Clear error messages and troubleshooting

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r ui/requirements.txt
```

### 2. Start Hot Path Service (Required)
```bash
cd hot_path
cargo run
```

### 3. Launch UI
```bash
python ui/run_ui.py
```

The UI will be available at: **http://localhost:8501**

## 📖 Usage Guide

### Creating a New Pattern

1. **Navigate to Pattern Creation** (🎨 Pattern Creation)
2. **Fill in the 6-Level Hierarchy**:
   - **Domain**: `child_development`, `self_state`, `relationship`
   - **Area**: `sleep`, `feeding`, `play`, `conflict`
   - **Topic**: `nap`, `breastfeeding`, `meltdown`
   - **Theme**: `crib_nap`, `food_refusal`
   - **Focus**: `early_am`, `afternoon`, `evening` (temporal markers)
   - **Form**: `single_entry`, `recurring`, `shutdown`

3. **Add Pattern Details**:
   - Description for embedding
   - Select relevant mixins
   - Provide 3-5 sample texts

4. **Validate and Save**:
   - Preview generated pattern
   - Validate against schema
   - Save to patterns directory
   - Reload hot path patterns

### Testing Classification

1. **Navigate to Classification Chat** (💬 Classification Chat)
2. **Enter text to classify**: "She went down for her early morning nap without fuss"
3. **View results**:
   - Best match with confidence score
   - Alternative matches
   - Processing time
4. **Check chat history** for previous classifications

## 🏗️ Architecture

```
┌─────────────────┐    HTTP/JSON    ┌──────────────────┐
│   Streamlit UI  │ ←─────────────→ │  Rust Hot Path   │
│   (Port 8501)   │                 │   (Port 3000)    │
└─────────────────┘                 └──────────────────┘
         │                                    │
         │ File I/O                          │ In-Memory
         ▼                                    ▼
┌─────────────────┐                 ┌──────────────────┐
│  Pattern Files  │                 │ Vector Store     │
│   (YAML)        │                 │ (Embeddings)     │
└─────────────────┘                 └──────────────────┘
```

### Component Integration

- **UI**: Streamlit web interface (Python)
- **Cold Path**: Pattern creation and validation (Python)
- **Hot Path**: Real-time classification (Rust)
- **Storage**: YAML files + in-memory vector store

## 🎯 Pattern Creation Workflow

1. **Design Hierarchy** using the 6-level structure
2. **Add Temporal Markers** when time context matters
3. **Validate Schema** compliance
4. **Test Classification** with sample texts
5. **Iterate** based on classification results

## 📊 Pattern Statistics

The UI automatically tracks:
- Total patterns in collection
- Domain distribution
- Temporal marker coverage
- Classification accuracy metrics

## 🔧 Troubleshooting

### Hot Path Service Not Running
```
❌ Hot path service not running
Start with: cd hot_path && cargo run
```

### Pattern Validation Errors
- Check hierarchy depth (2-6 levels)
- Ensure required fields are filled
- Verify sample texts are provided

### Classification Not Working
- Verify hot path service is running on port 3000
- Check pattern reload after creating new patterns
- Ensure patterns have embeddings

## 🔗 Integration Points

### API Endpoints Used
- `GET /health` - Service health check
- `GET /status` - System status and statistics
- `POST /classify` - Text classification
- `POST /reload-patterns` - Reload pattern index

### File Structure
```
ui/
├── app.py              # Main Streamlit application
├── run_ui.py           # Launcher script
├── requirements.txt    # Python dependencies
└── README.md          # This file

cold_path/
└── patterns/          # Pattern YAML files (created via UI)

hot_path/
└── target/           # Rust service (must be running)
```

## 🎨 UI Features

### Modern Design
- Gradient headers and modern styling
- Color-coded result cards
- Responsive layout
- Interactive forms

### Real-time Feedback
- Instant pattern validation
- Live hierarchy breakdown
- Real-time system status
- Performance metrics

### User Experience
- Guided pattern creation
- Clear error messages
- Persistent chat history
- Quick action buttons

## 📈 Performance

- **Classification**: Sub-millisecond response times
- **Pattern Creation**: Instant validation and preview
- **Real-time Updates**: Live system status monitoring
- **Scalability**: Handles hundreds of patterns efficiently

## 🔄 Development Workflow

1. **Create patterns** using the UI
2. **Test classification** in chat interface
3. **Monitor performance** via system status
4. **Iterate patterns** based on results
5. **Export/backup** pattern collection

The UI provides a complete development environment for building and testing pattern classification systems without requiring command-line expertise. 