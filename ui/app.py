"""
🧠 Familiar Classifier - Schema-Driven Classification Interface

This is a completely schema-driven UI that automatically adapts to JSON schema changes,
ensuring consistency with the hot path auto-generation system. Patterns are generated
by the cold path system, not manually created.
"""

import streamlit as st
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

# Add the parent directory to Python path so we can import modules
current_dir = Path(__file__).parent.absolute()
parent_dir = current_dir.parent.absolute()

# Add both the project root and current directory to path
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir))

try:
    from schema_driven_ui import SchemaUIGenerator
except ImportError as e:
    st.error(f"Failed to import modules: {e}")
    st.error(f"Current working directory: {os.getcwd()}")
    st.error(f"UI directory: {current_dir}")
    st.error(f"Project root: {parent_dir}")
    st.error(f"Python path: {sys.path[:5]}...")  # Show first 5 entries
    
    # Check if cold_path exists
    cold_path_dir = parent_dir / "cold_path"
    st.error(f"Cold path directory exists: {cold_path_dir.exists()}")
    if cold_path_dir.exists():
        st.error(f"Cold path contents: {list(cold_path_dir.iterdir())}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="🧠 Familiar Classifier (Schema-Driven)",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .metrics-card {
        background: #e8f5e9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    
    .error-card {
        background: #ffebee;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'schema_generator' not in st.session_state:
    st.session_state.schema_generator = SchemaUIGenerator()

def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🧠 Familiar Classifier</h1>
        <p>Schema-Driven Pattern Classification & Analysis</p>
        <small>✨ Clean chat interface with metrics analysis</small>
    </div>
    """, unsafe_allow_html=True)

def render_simple_chat():
    """Render a clean, simple chat interface focused on metrics."""
    st.header("💬 Classification Chat")
    
    generator = st.session_state.schema_generator
    
    # Simple input form
    with st.container():
        request_data = generator.generate_simple_chat_input()
        
        if st.button("🚀 Classify", type="primary", disabled=not request_data):
            with st.spinner("🔍 Classifying..."):
                result = generator.call_api("/classify", data=request_data)
                
                if result:
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "input": request_data["weaveUnit"]["text"],
                        "result": result,
                        "timestamp": "now",
                    })
                    st.rerun()
    
    # Chat history
    st.markdown("### 📜 Classification History")
    
    if not st.session_state.chat_history:
        st.info("💬 No classifications yet. Enter some text above to get started!")
        return
    
    # Show recent results
    for i, chat in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10
        with st.container():
            st.markdown('<div class="chat-message">', unsafe_allow_html=True)
            
            # Input text
            st.markdown(f"**💬 Input:** {chat['input']}")
            
            # Response with metrics
            generator.display_simple_response(chat['result'])
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if i < len(st.session_state.chat_history) - 1:
                st.markdown("---")
    
    # Clear history
    if st.button("🗑️ Clear History"):
        st.session_state.chat_history = []
        st.rerun()

# Pattern creation functionality removed - using cold path generation only
        
def render_schema_browser():
    """Render schema and pattern browser."""
    st.header("🌳 Schema & Pattern Browser")
    
    generator = st.session_state.schema_generator
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 All Schemas", "🌳 Pattern Tree", "📊 Level Schemas", "🔍 Raw JSON"])
    
    with tab1:
        st.subheader("📋 Available Schemas")
        
        models = generator.get_available_models()
        for model_name in models:
            model_info = generator.get_model_info(model_name)
            if model_info:
                with st.expander(f"📄 {model_name} ({len(model_info.fields)} fields)"):
                    st.markdown(f"**Description**: {model_info.description}")
                    st.markdown(f"**Required Fields**: {len(model_info.required_fields)}")
                    
                    # Show fields in a table format
                    field_data = []
                    for field in model_info.fields:
                        field_data.append({
                            "Field": field.name,
                            "Type": field.field_type,
                            "Required": "✅" if field.required else "❌",
                            "Default": str(field.default) if field.default is not None else "None",
                            "Description": field.description[:50] + "..." if len(field.description) > 50 else field.description
                        })
                    
                    if field_data:
                        st.table(field_data)
    
    with tab2:
        st.subheader("🌳 Pattern Hierarchy Tree")
        
        # Load patterns from assets directory (one level up from ui)
        try:
            patterns_file = Path("../assets/patterns_with_embeddings.json")
            
            if patterns_file.exists():
                file_size = patterns_file.stat().st_size / 1024  # KB
                st.success(f"✅ Found patterns file ({file_size:.1f} KB)")
                
                with open(patterns_file) as f:
                    patterns = json.load(f)
                
                if patterns and isinstance(patterns, list):
                    st.success(f"✅ Loaded {len(patterns)} patterns")
                    
                    # Build hierarchy tree
                    hierarchy = {}
                    for pattern in patterns:
                        pattern_id = pattern.get("id", "")
                        if "/" in pattern_id:
                            parts = pattern_id.split("/")
                            current = hierarchy
                            for i, part in enumerate(parts):
                                if part not in current:
                                    current[part] = {}
                                if i == len(parts) - 1:
                                    # Leaf node - store pattern data
                                    current[part]["_pattern_data"] = pattern
                                current = current[part]
                    
                    # Simple hierarchical display using indentation and buttons
                    def display_simple_tree(tree, level=0, path=""):
                        level_icons = ["🌍", "📂", "📄", "🎨", "🔍", "📋"]
                        
                        for key, value in tree.items():
                            if key == "_pattern_data":
                                continue
                            
                            current_path = f"{path}/{key}" if path else key
                            indent = "　" * level  # Using full-width space for indentation
                            icon = level_icons[level] if level < len(level_icons) else "📌"
                            
                            # Initialize session state for this node
                            expand_key = f"expand_{current_path.replace('/', '_')}"
                            if expand_key not in st.session_state:
                                st.session_state[expand_key] = False
                            
                            if "_pattern_data" in value:
                                # This is a leaf node (final pattern)
                                pattern_data = value["_pattern_data"]
                                
                                # Pattern toggle button
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    if st.button(f"{indent}{icon} **{key}** (Pattern)", key=f"btn_{expand_key}"):
                                        st.session_state[expand_key] = not st.session_state[expand_key]
                                
                                # Show pattern details if expanded
                                if st.session_state[expand_key]:
                                    st.markdown(f"{indent}　📋 **ID**: `{pattern_data.get('id', 'Unknown')}`")
                                    st.markdown(f"{indent}　📝 **Description**: {pattern_data.get('description', 'No description')}")
                                    
                                    sample_texts = pattern_data.get('sample_texts', [])
                                    if sample_texts:
                                        st.markdown(f"{indent}　💬 **Sample Texts** ({len(sample_texts)}):")
                                        for i, text in enumerate(sample_texts[:3]):
                                            st.markdown(f"{indent}　　{i+1}. *{text}*")
                                        if len(sample_texts) > 3:
                                            st.markdown(f"{indent}　　... and {len(sample_texts) - 3} more")
                                    
                                    if 'metadata' in pattern_data and pattern_data['metadata']:
                                        st.markdown(f"{indent}　🏷️ **Metadata**: {pattern_data['metadata']}")
                            else:
                                # This is a branch node
                                child_count = len([k for k in value.keys() if k != "_pattern_data"])
                                
                                # Branch toggle button
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    if st.button(f"{indent}{icon} **{key}** ({child_count} items)", key=f"btn_{expand_key}"):
                                        st.session_state[expand_key] = not st.session_state[expand_key]
                                
                                # Show children if expanded
                                if st.session_state[expand_key]:
                                    display_simple_tree(value, level + 1, current_path)
                    
                    # Display the tree
                    st.markdown("### 🌳 Pattern Hierarchy (Click to expand/collapse)")
                    
                    # Add expand/collapse all buttons
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        if st.button("📖 Expand All"):
                            for key in st.session_state:
                                if key.startswith("expand_"):
                                    st.session_state[key] = True
                            st.rerun()
                    with col2:
                        if st.button("📕 Collapse All"):
                            for key in st.session_state:
                                if key.startswith("expand_"):
                                    st.session_state[key] = False
                            st.rerun()
                    
                    display_simple_tree(hierarchy)
                else:
                    st.error("No patterns found in the data")
            else:
                st.warning(f"Pattern file not found: {patterns_file.absolute()}")
                st.info("Generate patterns first using the hot path service")
        except Exception as e:
            st.error(f"Error loading patterns: {e}")
    
    with tab3:
        st.subheader("📊 Level Schemas")
        
        # Load level schemas from assets directory
        try:
            level_schemas_file = Path("../assets/level_schemas_with_embeddings.json")
            
            if level_schemas_file.exists():
                file_size = level_schemas_file.stat().st_size / 1024  # KB
                st.success(f"✅ Found level schemas file ({file_size:.1f} KB)")
                
                with open(level_schemas_file) as f:
                    level_schemas = json.load(f)
                
                if level_schemas and isinstance(level_schemas, list):
                    st.success(f"✅ Loaded {len(level_schemas)} level schemas")
                    
                    for level_info in level_schemas:
                        level_name = level_info.get('name', level_info.get('id', 'Unknown'))
                        with st.expander(f"📊 Level: {level_name}"):
                            st.markdown(f"**Description**: {level_info.get('description', 'No description')}")
                            
                            # Show examples if available
                            examples = level_info.get('examples', level_info.get('values', []))
                            if examples:
                                st.markdown(f"**Examples** ({len(examples)}):")
                                cols = st.columns(3)
                                for i, example in enumerate(examples[:9]):  # Show max 9 examples
                                    with cols[i % 3]:
                                        st.code(example)
                            
                            # Show embedding info
                            if 'embedding' in level_info:
                                st.markdown(f"**Has Embedding**: ✅ ({len(level_info['embedding'])} dimensions)")
                else:
                    st.error("No level schemas found in the data")
            else:
                st.warning(f"Level schemas file not found: {level_schemas_file.absolute()}")
        except Exception as e:
            st.error(f"Error loading level schemas: {e}")
    
    with tab4:
        st.subheader("🔍 Raw JSON Schemas")
        
        # Display the raw JSON schema
        if generator.schemas:
            st.markdown("**Main Schema Structure:**")
            st.json(generator.schemas)
            
            # Add download button for schemas
            schema_json = json.dumps(generator.schemas, indent=2)
            st.download_button(
                label="💾 Download schemas.json",
                data=schema_json,
                file_name="schemas.json",
                mime="application/json"
            )
            
            # Show file locations
            st.markdown("---")
            st.subheader("📁 File Locations")
            st.markdown("The following files are available in the `assets/` directory:")
            
            assets_dir = Path("../assets")
            if assets_dir.exists():
                for file_path in assets_dir.glob("*.json"):
                    file_size = file_path.stat().st_size / 1024  # KB
                    st.markdown(f"- `{file_path.name}` ({file_size:.1f} KB)")
        else:
            st.error("No schemas loaded")

def render_system_status():
    """Render system status and metrics."""
    st.header("📊 System Status & Metrics")
    
    generator = st.session_state.schema_generator
    
    # System health
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Service Health")
        
        # Hot path status
        status = generator.call_api("/status")
        if status and isinstance(status, dict):
            st.success("✅ Hot Path Online")
            st.json(status)
        else:
            st.error("❌ Hot Path Offline")
        
        # Health check
        if st.button("🏥 Health Check"):
            result = generator.call_api("/health")
            if result and (result.get("message") == "OK" or result == "OK"):
                st.success("✅ System healthy!")
            else:
                st.error("❌ Health check failed")
        
    with col2:
        st.subheader("📈 Chat Metrics")
        
        if st.session_state.chat_history:
            total_chats = len(st.session_state.chat_history)
            
            # Calculate success rate
            successful = sum(1 for chat in st.session_state.chat_history 
                           if chat["result"].get("status") == "success")
            success_rate = (successful / total_chats) * 100 if total_chats > 0 else 0
            
            # Calculate average processing time
            processing_times = [chat["result"].get("processingTimeMs", 0) 
                              for chat in st.session_state.chat_history 
                              if chat["result"].get("processingTimeMs")]
            avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Display metrics
            st.metric("Total Classifications", total_chats)
            st.metric("Success Rate", f"{success_rate:.1f}%")
            st.metric("Avg Processing Time", f"{avg_time:.1f}ms")
            
            # Pattern matches
            matches = [chat["result"].get("matchResult") 
                      for chat in st.session_state.chat_history 
                      if chat["result"].get("matchResult")]
            st.metric("Successful Matches", len(matches))
        else:
            st.info("No chat history yet")

def main():
    """Main schema-driven application."""
    render_header()
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["💬 Classification Chat", "🌳 Schema Browser", "📊 System Status"]
    )
    
    if page == "💬 Classification Chat":
        render_simple_chat()
    elif page == "🌳 Schema Browser":
        render_schema_browser()
    elif page == "📊 System Status":
        render_system_status()
    
    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Schema-Driven Features")
    st.sidebar.markdown("✅ Auto-generated from JSON schemas")
    st.sidebar.markdown("✅ Success/failure analysis")
    st.sidebar.markdown("✅ Performance metrics")
    st.sidebar.markdown("✅ Clean chat interface")
    
    st.sidebar.markdown("### 🔗 Quick Links")
    st.sidebar.markdown("- [Hot Path Service](http://localhost:3000)")
    st.sidebar.markdown("- [JSON Schemas](../assets/schemas.json)")
    
    # Schema debug
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🐛 Schema Debug")
    generator = st.session_state.schema_generator
    
    if st.sidebar.button("🔧 Test Schema"):
        models = generator.get_available_models()
        st.sidebar.write(f"✅ Loaded {len(models)} models")

if __name__ == "__main__":
    main() 