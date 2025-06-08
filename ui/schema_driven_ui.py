"""
Schema-Driven UI Generator for Familiar Classifier

This module automatically generates Streamlit UI components from JSON schemas,
ensuring consistency with the hot path auto-generation and eliminating manual
field name maintenance.
"""

import streamlit as st
import json
import requests
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

@dataclass
class SchemaField:
    """Represents a field definition from JSON schema."""
    name: str
    field_type: str
    required: bool
    default: Any = None
    description: str = ""
    enum_values: List[str] = None
    minimum: float = None
    maximum: float = None
    items_type: str = None

@dataclass 
class SchemaModel:
    """Represents a complete model from JSON schema."""
    name: str
    description: str
    fields: List[SchemaField]
    required_fields: List[str]

class SchemaUIGenerator:
    """Generates Streamlit UI components from JSON schemas."""
    
    def __init__(self, schema_path: str = "../assets/schemas.json"):
        # Simple path resolution - UI runs from ui directory, assets is one level up
        self.schema_path = Path("../assets/schemas.json")
        self.schemas = self._load_schemas()
        self.models = self._parse_models()
    
    def _load_schemas(self) -> Dict[str, Any]:
        """Load schemas from JSON file."""
        try:
            with open(self.schema_path) as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Failed to load schemas from {self.schema_path}: {e}")
            return {}
    
    def _parse_models(self) -> Dict[str, SchemaModel]:
        """Parse JSON schema models into structured format."""
        models = {}
        
        if "models" not in self.schemas:
            return models
            
        for model_name, model_def in self.schemas["models"].items():
            if "properties" not in model_def:
                continue
                
            fields = []
            required_fields = model_def.get("required", [])
            
            for field_name, field_def in model_def["properties"].items():
                field = self._parse_field(field_name, field_def, field_name in required_fields)
                fields.append(field)
            
            models[model_name] = SchemaModel(
                name=model_name,
                description=model_def.get("description", ""),
                fields=fields,
                required_fields=required_fields
            )
        
        return models
    
    def _parse_field(self, name: str, field_def: Dict[str, Any], required: bool) -> SchemaField:
        """Parse a single field definition."""
        # Handle $ref references
        if "$ref" in field_def:
            ref_path = field_def["$ref"]
            if ref_path.startswith("#/$defs/"):
                ref_name = ref_path.split("/")[-1]
                # Look up the referenced type
                return SchemaField(
                    name=name,
                    field_type="object",
                    required=required,
                    description=field_def.get("description", f"Reference to {ref_name}")
                )
        
        # Handle anyOf (optional fields)
        if "anyOf" in field_def:
            # Find the non-null type
            for option in field_def["anyOf"]:
                if option.get("type") != "null":
                    field_def = option
                    break
        
        field_type = field_def.get("type", "string")
        enum_values = field_def.get("enum")
        default = field_def.get("default")
        
        # Handle array types
        items_type = None
        if field_type == "array" and "items" in field_def:
            items_def = field_def["items"]
            if "$ref" in items_def:
                items_type = "object"
            else:
                items_type = items_def.get("type", "string")
        
        return SchemaField(
            name=name,
            field_type=field_type,
            required=required,
            default=default,
            description=field_def.get("description", ""),
            enum_values=enum_values,
            minimum=field_def.get("minimum"),
            maximum=field_def.get("maximum"),
            items_type=items_type
        )
    
    def generate_simple_chat_input(self) -> Dict[str, Any]:
        """Generate a simple chat input for classification."""
        user_input = st.text_area(
            "💬 Enter text to classify:",
            placeholder="She went down for her early morning nap without fuss...",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            confidence_threshold = st.slider("Confidence Threshold", 0.01, 1.0, 0.3, 0.01)
        with col2:
            max_alternatives = st.slider("Max Alternatives", 1, 10, 3, 1)
        
        if user_input.strip():
            return {
                "weaveUnit": {"text": user_input},
                "maxAlternatives": max_alternatives,
                "confidenceThreshold": confidence_threshold,
            }
        return {}
    
    def display_simple_response(self, response: Dict[str, Any]):
        """Display classification response in a clean chat format."""
        status = response.get("status", "unknown")
        
        # Status indicator
        if status == "success":
            st.success("✅ Classification Complete")
        elif status == "error":
            st.error(f"❌ Error: {response.get('errorMessage', 'Unknown error')}")
            return
        
        # Metrics row
        col1, col2, col3 = st.columns(3)
        with col1:
            processing_time = response.get("processingTimeMs", 0)
            st.metric("⚡ Speed", f"{processing_time:.1f}ms")
        
        with col2:
            match = response.get("matchResult")
            if match:
                confidence = match.get("confidence", 0) * 100
                st.metric("🎯 Confidence", f"{confidence:.1f}%")
            else:
                st.metric("🎯 Confidence", "No match")
        
        with col3:
            alternatives = response.get("alternatives", [])
            st.metric("🔄 Alternatives", len(alternatives))
        
        # Classification steps (hierarchical progression)
        if "classificationSteps" in response and response["classificationSteps"]:
            with st.expander("🏗️ Classification Steps", expanded=True):
                for step in response["classificationSteps"]:
                    st.markdown(f"- {step}")
        
        # Best match
        if match:
            st.markdown("**🎯 Best Match:**")
            pattern_id = match.get("patternId", "Unknown")
            st.code(pattern_id)
            
            # Show alternatives if any
            if alternatives:
                with st.expander(f"🔄 {len(alternatives)} Alternatives"):
                    for i, alt in enumerate(alternatives, 1):
                        alt_pattern = alt.get("patternId", "Unknown")
                        alt_conf = alt.get("confidence", 0) * 100
                        st.markdown(f"{i}. `{alt_pattern}` ({alt_conf:.1f}%)")
        else:
            st.warning("🤷 No pattern match found above threshold")
    
    def generate_form(self, model_name: str, key_prefix: str = "") -> Dict[str, Any]:
        """Generate a Streamlit form for the given model."""
        if model_name not in self.models:
            st.error(f"Model {model_name} not found in schemas")
            return {}
        
        model = self.models[model_name]
        form_data = {}
        
        st.markdown(f"### {model.description}")
        
        for field in model.fields:
            field_key = f"{key_prefix}{field.name}"
            value = self._generate_field_input(field, field_key)
            
            # Convert camelCase to snake_case for internal use, then back to camelCase
            form_data[field.name] = value
        
        return form_data
    
    def _generate_field_input(self, field: SchemaField, key: str) -> Any:
        """Generate input widget for a specific field."""
        label = field.name.replace("_", " ").title()
        help_text = field.description
        
        if field.enum_values:
            # Enum/select field
            options = field.enum_values
            default_idx = 0
            if field.default and field.default in options:
                default_idx = options.index(field.default)
            return st.selectbox(label, options, index=default_idx, help=help_text, key=key)
        
        elif field.field_type == "string":
            # String field
            default_val = field.default or ""
            return st.text_input(label, value=default_val, help=help_text, key=key)
        
        elif field.field_type == "number":
            # Number field
            min_val = field.minimum if field.minimum is not None else 0.0
            max_val = field.maximum if field.maximum is not None else 1.0
            default_val = field.default if field.default is not None else min_val
            step = 0.01 if max_val <= 1.0 else 1.0
            return st.slider(label, min_val, max_val, default_val, step, help=help_text, key=key)
        
        elif field.field_type == "integer":
            # Integer field
            min_val = int(field.minimum) if field.minimum is not None else 1
            max_val = int(field.maximum) if field.maximum is not None else 10
            default_val = int(field.default) if field.default is not None else min_val
            return st.slider(label, min_val, max_val, default_val, 1, help=help_text, key=key)
        
        elif field.field_type == "boolean":
            # Boolean field
            default_val = field.default if field.default is not None else False
            return st.checkbox(label, value=default_val, help=help_text, key=key)
        
        elif field.field_type == "array":
            # Array field - simplified for now
            if field.items_type == "string":
                st.markdown(f"**{label}**")
                if help_text:
                    st.caption(help_text)
                items = []
                for i in range(5):  # Allow up to 5 items
                    item = st.text_input(f"Item {i+1}", key=f"{key}_item_{i}")
                    if item.strip():
                        items.append(item.strip())
                return items
            else:
                return []
        
        elif field.field_type == "object":
            # Object field - handle nested objects
            if field.name == "weaveUnit":
                return self._generate_weave_unit_form(key)
            else:
                st.markdown(f"**{label}** (Object)")
                return {}
        
        else:
            # Fallback to text input
            return st.text_input(label, help=help_text, key=key)
    
    def _generate_weave_unit_form(self, key: str) -> Dict[str, Any]:
        """Generate form for WeaveUnit specifically."""
        if "WeaveUnit" not in self.models:
            return {"text": st.text_input("Text", key=f"{key}_text")}
        
        weave_unit_model = self.models["WeaveUnit"]
        weave_data = {}
        
        for field in weave_unit_model.fields:
            if field.name == "text":
                # Main text input
                weave_data["text"] = st.text_area(
                    "Text to classify",
                    placeholder="Enter text to classify...",
                    help=field.description,
                    key=f"{key}_text"
                )
            elif field.name == "metadata":
                # Skip metadata for now - could be expanded
                weave_data["metadata"] = {}
            # Skip id and timestamp - they're auto-generated
        
        return weave_data
    
    def display_response(self, response: Dict[str, Any], model_name: str = "ClassificationResponse"):
        """Display API response using schema-driven formatting."""
        if model_name not in self.models:
            st.json(response)
            return
        
        model = self.models[model_name]
        
        # Handle success/error status
        status = response.get("status", "unknown")
        if status == "success":
            st.success("✅ Classification successful")
        elif status == "error":
            st.error(f"❌ Error: {response.get('errorMessage', 'Unknown error')}")
        
        # Display processing time
        if "processingTimeMs" in response:
            st.metric("⚡ Processing Time", f"{response['processingTimeMs']:.2f}ms")
        
        # Display classification steps
        if "classificationSteps" in response and response["classificationSteps"]:
            st.markdown("**🏗️ Hierarchical Classification Steps:**")
            for step in response["classificationSteps"]:
                st.markdown(f"- {step}")
        
        # Display match result
        if "matchResult" in response and response["matchResult"]:
            match = response["matchResult"]
            st.markdown("**🎯 Best Match**")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                pattern_id = match.get("patternId", "Unknown")
                st.code(pattern_id)
            with col2:
                confidence = match.get("confidence", 0) * 100
                st.metric("Confidence", f"{confidence:.2f}%")
            
            # Display metadata if present
            if "metadata" in match and match["metadata"]:
                with st.expander("📋 Metadata"):
                    st.json(match["metadata"])
        
        # Display alternatives
        if "alternatives" in response and response["alternatives"]:
            st.markdown("**🔄 Alternative Matches**")
            for i, alt in enumerate(response["alternatives"], 1):
                pattern_id = alt.get("patternId", "Unknown")
                confidence = alt.get("confidence", 0) * 100
                st.markdown(f"{i}. `{pattern_id}` ({confidence:.2f}%)")
    
    def call_api(self, endpoint: str, data: Dict[str, Any] = None, method: str = "auto", expect_json: bool = True) -> Optional[Union[Dict[str, Any], str]]:
        """Call the hot path API with error handling."""
        try:
            url = f"http://localhost:3000{endpoint}"
            
            if data is not None or method == "POST":
                response = requests.post(url, json=data or {}, headers={"Content-Type": "application/json"}, timeout=10)
            else:
                response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                if expect_json:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        return {"status": "success", "message": response.text.strip()}
                else:
                    return response.text.strip()
            else:
                st.error(f"API Error {response.status_code}: {response.text}")
                return None
        except requests.exceptions.ConnectionError:
            st.error("🔌 Hot path service not running. Start with: `cd hot_path && cargo run`")
            return None
        except Exception as e:
            st.error(f"API call failed: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Get list of available schema models."""
        return list(self.models.keys())
    
    def get_model_info(self, model_name: str) -> Optional[SchemaModel]:
        """Get detailed information about a specific model."""
        return self.models.get(model_name) 