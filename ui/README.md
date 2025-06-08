# 🧠 Familiar Classifier - Schema-Driven UI

A **completely schema-driven** Streamlit interface that automatically generates forms and displays from JSON schemas, ensuring perfect consistency with the hot path API.

## ✨ Key Features

- **🤖 Auto-Generated Forms**: UI components generated from JSON schemas
- **🔄 Zero Schema Drift**: Automatic adaptation to schema changes  
- **🎯 Perfect Consistency**: Same field names/types as hot path API
- **⚡ Real-Time Classification**: Live hierarchical pattern matching
- **📊 Schema Debugging**: Built-in schema inspection tools

## 🚀 Quick Start

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt
```

### Run the System
```bash
# Terminal 1: Start hot path service
cd ../hot_path && cargo run --release

# Terminal 2: Start schema-driven UI
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## 🏗️ Architecture

### Schema-Driven Generation
```
assets/schemas.json ──┐
                      ├──> hot_path/build.rs ──> Rust Structs
                      └──> ui/schema_driven_ui.py ──> Streamlit Forms
```

### Components

- **`app.py`**: Main schema-driven application
- **`schema_driven_ui.py`**: Automatic UI generator from JSON schemas
- **`requirements.txt`**: Python dependencies

## 🔧 How It Works

### 1. **Schema Loading**
```python
generator = SchemaUIGenerator()
# Automatically loads and parses assets/schemas.json
```

### 2. **Form Generation**
```python
# Generates form from ClassificationRequest schema
request_data = generator.generate_form("ClassificationRequest")
```

### 3. **Response Display**
```python
# Displays response using ClassificationResponse schema
generator.display_response(api_result)
```

## 📋 Available Schemas

The UI automatically detects and generates forms for:

- **PatternSchema**: Pattern creation and validation
- **ClassificationRequest**: Classification input forms
- **ClassificationResponse**: Result display formatting
- **WeaveUnit**: Text input with metadata
- **PatternMixin**: Enum selections

## 🛠️ Schema-Driven Features

### Automatic Field Types
- **String fields** → Text inputs
- **Number fields** → Sliders with min/max from schema
- **Boolean fields** → Checkboxes
- **Enum fields** → Select boxes
- **Object fields** → Nested forms
- **Array fields** → Dynamic lists

### Smart Defaults
- Uses schema `default` values
- Applies field descriptions as help text
- Validates required vs optional fields
- Handles camelCase ↔ snake_case conversion

### Real-Time Adaptation
When you update `assets/schemas.json`:
1. **Hot path rebuilds** automatically (Rust structs)
2. **UI updates** automatically (Python forms)
3. **Zero code changes** needed

## 🧪 Testing

### API Health Check
```bash
curl http://localhost:3000/health
# Should return: OK
```

### Schema-Driven Classification
```bash
curl -X POST http://localhost:3000/classify \
  -H "Content-Type: application/json" \
  -d '{
    "weaveUnit": {"text": "she took a long nap"},
    "maxAlternatives": 3,
    "confidenceThreshold": 0.3
  }'
```

### UI Schema Debug
1. Open the UI at [http://localhost:8501](http://localhost:8501)
2. Check the sidebar "Schema Debug Panel"
3. View loaded models and field definitions

## 🔍 Debugging

### Schema Loading Issues
```python
# Test schema loading directly
python -c "from schema_driven_ui import SchemaUIGenerator; gen = SchemaUIGenerator(); print(f'Loaded {len(gen.get_available_models())} models')"
```

### API Connection Issues
```python
# Test API connection
python -c "import requests; r = requests.get('http://localhost:3000/health'); print(f'API: {r.text}')"
```

## 📊 Schema Information

The UI displays real-time schema information:
- **Schema Version**: From `assets/schemas.json`
- **Available Models**: Auto-detected from schema
- **Field Counts**: Required vs optional fields
- **Generation Source**: Shows schema origin

## 🚀 Benefits Over Manual UI

| Manual Approach | Schema-Driven |
|-----------------|---------------|
| ❌ Hardcoded fields | ✅ Auto-generated |
| ❌ Field name mismatches | ✅ Perfect consistency |
| ❌ Manual updates needed | ✅ Automatic adaptation |
| ❌ Error-prone | ✅ Schema-validated |
| ❌ Maintenance burden | ✅ Zero maintenance |

## 🔮 Future Enhancements

- **Multi-language support** (TypeScript, Go, etc.)
- **Advanced validation** (regex patterns, custom rules)
- **Theme customization** (schema-driven styling)
- **Real-time collaboration** (shared schema updates)

---

**Built with ❤️ using schema-driven architecture - because consistency matters!** 