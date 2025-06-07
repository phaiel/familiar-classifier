"""
🧠 Familiar Classifier - Pattern Creation & Chat Interface
Modern web UI for creating patterns and testing classification
"""

import streamlit as st
import requests
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

# Add the parent directory to Python path so we can import from cold_path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from cold_path.schemas import PatternSchema, PatternMixin, WeaveUnit, ClassificationRequest
except ImportError as e:
    st.error(f"Failed to import cold_path modules: {e}")
    st.error(f"Current working directory: {os.getcwd()}")
    st.error(f"Python path: {sys.path}")
    st.error(f"Parent directory: {parent_dir}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="🧠 Familiar Classifier",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
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
    
    .pattern-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .classification-result {
        background: #e8f5e9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    
    .error-result {
        background: #ffebee;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
    }
    
    .hierarchy-level {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        margin: 0.2rem;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'patterns' not in st.session_state:
    st.session_state.patterns = []

def load_existing_patterns():
    """Load existing patterns from the patterns directory."""
    # Get absolute path to patterns directory
    current_dir = Path(__file__).parent.parent  # Go up to project root
    patterns_dir = current_dir / "cold_path" / "patterns"
    patterns = []
    
    if patterns_dir.exists():
        yaml_files = list(patterns_dir.rglob("*.yaml"))
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)
                    if data:
                        patterns.append(data)
            except Exception as e:
                st.error(f"Error loading {yaml_file.name}: {e}")
    else:
        st.warning(f"Patterns directory not found: {patterns_dir}")
        st.info(f"Current working directory: {os.getcwd()}")
        st.info(f"Looking for patterns in: {patterns_dir.absolute()}")
    
    return patterns

def save_pattern(pattern_data: Dict[str, Any]) -> bool:
    """Save a pattern to the patterns directory."""
    try:
        pattern_id = pattern_data['id']
        # Get absolute path to patterns directory
        current_dir = Path(__file__).parent.parent  # Go up to project root
        patterns_dir = current_dir / "cold_path" / "patterns"
        
        # Create directory structure from pattern ID
        pattern_path = patterns_dir / (pattern_id.replace('/', '/') + '.yaml')
        pattern_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(pattern_path, 'w') as f:
            yaml.dump(pattern_data, f, default_flow_style=False, sort_keys=False)
        
        return True
    except Exception as e:
        st.error(f"Error saving pattern: {e}")
        return False

def call_hot_path_api(endpoint: str, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Call the Rust hot path API."""
    try:
        url = f"http://localhost:3000{endpoint}"
        # st.write(f"🔗 Calling API: {url}")  # Debug info - commented out to reduce noise
        if data:
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Hot path service not running. Start with: `cd hot_path && cargo run`")
        return None
    except Exception as e:
        st.error(f"API call failed: {e}")
        return None

def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🧠 Familiar Classifier</h1>
        <p>Pattern Creation & Classification Testing Interface</p>
    </div>
    """, unsafe_allow_html=True)

def render_pattern_creation_page():
    """Render the pattern creation interface."""
    st.header("🎨 Pattern Creation")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Pattern Definition")
        
        # 6-level hierarchy input
        st.markdown("### 🏗️ 6-Level Hierarchy")
        domain = st.text_input("1. Domain", placeholder="self_state, child_development, relationship")
        area = st.text_input("2. Area", placeholder="sleep, feeding, play, conflict")
        topic = st.text_input("3. Topic", placeholder="nap, breastfeeding, meltdown")
        theme = st.text_input("4. Theme", placeholder="crib_nap, food_refusal")
        focus = st.text_input("5. Focus (⏰ Temporal)", placeholder="early_am, afternoon, evening")
        form = st.text_input("6. Form", placeholder="single_entry, recurring, shutdown")
        
        # Auto-generate pattern ID
        hierarchy_parts = [domain, area, topic, theme, focus, form]
        pattern_id = "/".join([part for part in hierarchy_parts if part.strip()])
        
        st.markdown("### 📋 Generated Pattern ID")
        st.code(pattern_id)
        
        # Show hierarchy breakdown
        if pattern_id:
            st.markdown("### 🔍 Hierarchy Breakdown")
            levels = ['Domain', 'Area', 'Topic', 'Theme', 'Focus', 'Form']
            parts = pattern_id.split('/')
            
            for i, (level, part) in enumerate(zip(levels, parts)):
                if i < len(parts):
                    st.markdown(f'<span class="hierarchy-level">{level}: {part}</span>', unsafe_allow_html=True)
        
        # Pattern details
        st.markdown("### 📝 Pattern Details")
        description = st.text_area("Description", placeholder="Human-readable description for embedding")
        
        # Mixins selection
        available_mixins = [mixin.value for mixin in PatternMixin]
        selected_mixins = st.multiselect("Mixins", available_mixins)
        
        # Sample texts
        st.markdown("### 💬 Sample Texts (Training Examples)")
        sample_texts = []
        for i in range(5):
            text = st.text_input(f"Sample Text {i+1}", key=f"sample_{i}")
            if text.strip():
                sample_texts.append(text.strip())
    
    with col2:
        st.subheader("Pattern Preview & Validation")
        
        if pattern_id and description and sample_texts:
            # Create pattern data
            pattern_data = {
                'id': pattern_id,
                'description': description,
                'mixins': selected_mixins,
                'sample_texts': sample_texts,
                'metadata': {
                    'created_via': 'ui',
                    'hierarchy_depth': len(pattern_id.split('/')),
                    'has_temporal': any(marker in pattern_id.lower() for marker in ['early_am', 'morning', 'midday', 'afternoon', 'evening', 'night'])
                }
            }
            
            # Validate pattern
            try:
                pattern = PatternSchema(**pattern_data)
                
                st.markdown('<div class="pattern-card">', unsafe_allow_html=True)
                st.markdown("### ✅ Pattern Valid!")
                st.json(pattern_data)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Save button
                if st.button("💾 Save Pattern", type="primary"):
                    if save_pattern(pattern_data):
                        st.success(f"✅ Pattern saved: {pattern_id}")
                        # Reload patterns index
                        if st.button("🔄 Reload Hot Path Patterns"):
                            result = call_hot_path_api("/reload-patterns")
                            if result:
                                st.success("🔥 Hot path patterns reloaded!")
                    else:
                        st.error("❌ Failed to save pattern")
                        
            except Exception as e:
                st.markdown('<div class="error-result">', unsafe_allow_html=True)
                st.markdown(f"### ❌ Validation Error")
                st.error(str(e))
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("👆 Fill in the pattern details to see preview")
        
        # Show existing patterns
        st.markdown("### 📚 Existing Patterns")
        existing_patterns = load_existing_patterns()
        
        if existing_patterns:
            st.info(f"Found {len(existing_patterns)} patterns")
            for pattern in existing_patterns:  # Show all patterns, not just first 5
                with st.expander(f"📄 {pattern.get('id', 'Unknown')}"):
                    st.json(pattern)
        else:
            st.info("No existing patterns found")

def render_chat_interface():
    """Render the chat classification interface."""
    st.header("💬 Classification Chat")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Chat Interface")
        
        # Chat input
        user_input = st.text_input("Enter text to classify:", placeholder="She went down for her early morning nap without fuss")
        
        col_send, col_clear = st.columns([1, 1])
        
        with col_send:
            if st.button("🚀 Classify", type="primary") and user_input:
                with st.spinner("🔍 Classifying..."):
                    # Call classification API (using camelCase to match Rust schema)
                    classification_data = {
                        "weaveUnit": {
                            "text": user_input,
                            "metadata": {}
                        },
                        "maxAlternatives": 3,
                        "confidenceThreshold": 0.5
                    }
                    
                    result = call_hot_path_api("/classify", classification_data)
                    
                    if result:
                        # Add to chat history
                        st.session_state.chat_history.append({
                            "input": user_input,
                            "result": result,
                            "timestamp": "now"
                        })
                        st.success("✅ Classification completed!")
                        st.rerun()  # Force UI refresh
                    else:
                        st.error("❌ Classification failed - check if hot path service is running")
        
        with col_clear:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
        
        # Display chat history
        st.markdown("### 📜 Classification History")
        
        for chat in reversed(st.session_state.chat_history):
            st.markdown("---")
            
            # User input
            st.markdown(f"**👤 Input:** {chat['input']}")
            
            # Classification result
            result = chat['result']
            
            if result.get('status') == 'success':
                match = result.get('matchResult')  # Updated field name
                if match:
                    confidence = match.get('confidence', 0) * 100
                    pattern_id = match.get('patternId', 'Unknown')  # Updated field name
                    
                    st.markdown('<div class="classification-result">', unsafe_allow_html=True)
                    st.markdown(f"**🎯 Best Match:** `{pattern_id}` ({confidence:.1f}% confidence)")
                    
                    # Show alternatives
                    alternatives = result.get('alternatives', [])
                    if alternatives:
                        st.markdown("**🔄 Alternatives:**")
                        for alt in alternatives:
                            alt_conf = alt.get('confidence', 0) * 100
                            st.markdown(f"- `{alt.get('patternId', 'Unknown')}` ({alt_conf:.1f}%)")  # Updated field name
                    
                    processing_time = result.get('processingTimeMs', 0)  # Updated field name
                    st.markdown(f"**⚡ Processing Time:** {processing_time:.2f}ms")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-result">', unsafe_allow_html=True)
                    st.markdown("**❌ No match found above confidence threshold**")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                error_msg = result.get('errorMessage', 'Unknown error')  # Updated field name
                st.markdown('<div class="error-result">', unsafe_allow_html=True)
                st.markdown(f"**❌ Classification Error:** {error_msg}")
                st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.subheader("🔍 System Status")
        
        # Check hot path status
        status = call_hot_path_api("/status")
        
        if status:
            st.markdown('<div class="classification-result">', unsafe_allow_html=True)
            st.markdown("### ✅ Hot Path Online")
            st.json(status)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-result">', unsafe_allow_html=True)
            st.markdown("### ❌ Hot Path Offline")
            st.markdown("Start with: `cd hot_path && cargo run`")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Reload Patterns"):
            result = call_hot_path_api("/reload-patterns")
            if result:
                st.success("Patterns reloaded!")
        
        if st.button("🏥 Health Check"):
            result = call_hot_path_api("/health")
            if result:
                st.success("System healthy!")
        
        # Pattern statistics
        st.markdown("### 📊 Pattern Stats")
        existing_patterns = load_existing_patterns()
        
        if existing_patterns:
            domains = {}
            temporal_count = 0
            
            for pattern in existing_patterns:
                pattern_id = pattern.get('id', '')
                domain = pattern_id.split('/')[0] if '/' in pattern_id else 'unknown'
                domains[domain] = domains.get(domain, 0) + 1
                
                if any(marker in pattern_id.lower() for marker in ['early_am', 'morning', 'afternoon', 'evening']):
                    temporal_count += 1
            
            st.metric("Total Patterns", len(existing_patterns))
            st.metric("Domains", len(domains))
            st.metric("With Temporal Markers", temporal_count)
            st.metric("Temporal Coverage", f"{temporal_count/len(existing_patterns)*100:.1f}%")

def main():
    """Main application."""
    render_header()
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["🎨 Pattern Creation", "💬 Classification Chat"]
    )
    
    if page == "🎨 Pattern Creation":
        render_pattern_creation_page()
    elif page == "💬 Classification Chat":
        render_chat_interface()
    
    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔗 Quick Links")
    st.sidebar.markdown("- [GitHub Repository](https://github.com/phaiel/familiar-classifier)")
    st.sidebar.markdown("- [Pattern Directory](../cold_path/patterns)")
    st.sidebar.markdown("- [Hot Path Service](http://localhost:3000)")
    
    st.sidebar.markdown("### 🛠️ System Commands")
    st.sidebar.code("cd hot_path && cargo run")
    st.sidebar.code("python -m cold_path.cli temporal-analysis")
    
    # Debug panel
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🐛 Debug Panel")
    if st.sidebar.button("🔧 Test API Connection"):
        with st.sidebar:
            st.write("Testing hot path API...")
            health = call_hot_path_api("/health")
            if health:
                st.success("✅ API connection working!")
                status = call_hot_path_api("/status")
                if status:
                    st.json(status.get("vector_store_stats", {}))
            else:
                st.error("❌ API connection failed!")
    
    if st.sidebar.button("📊 Check Patterns"):
        with st.sidebar:
            patterns = load_existing_patterns()
            st.write(f"Found {len(patterns)} patterns:")
            for p in patterns:
                st.write(f"- {p.get('id', 'Unknown')}")

if __name__ == "__main__":
    main() 