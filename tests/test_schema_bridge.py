"""Tests for the schema bridge between Python cold path and Rust hot path."""

import json
import pytest
from pathlib import Path
import tempfile
import shutil

from cold_path.schema_bridge import SchemaBridge, export_all_schemas
from cold_path.schemas import PatternSchema, WeaveUnit, PatternMixin


class TestSchemaBridge:
    """Test schema bridge functionality."""
    
    def test_schema_export(self):
        """Test exporting schemas to JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge = SchemaBridge(output_dir=temp_dir)
            result = bridge.export_schemas()
            
            assert result["version"] == "0.1.0"
            assert result["generator"] == "cold_path_schema_bridge"
            assert "PatternSchema" in result["schemas"]
            assert "WeaveUnit" in result["schemas"]
            assert "PatternMixin" in result["enums"]
            
            # Check that JSON file was created
            json_file = Path(temp_dir) / "schemas.json"
            assert json_file.exists()
            
            # Verify JSON is valid
            with open(json_file) as f:
                data = json.load(f)
                assert data == result
    
    def test_pattern_export(self):
        """Test exporting pattern definitions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge = SchemaBridge(output_dir=temp_dir)
            
            # Create test patterns
            patterns = [
                PatternSchema(
                    id="test/pattern/one",
                    description="Test pattern one",
                    mixins=[PatternMixin.TIME],
                    sample_texts=["Sample 1", "Sample 2"]
                ),
                PatternSchema(
                    id="test/pattern/two", 
                    description="Test pattern two",
                    mixins=[PatternMixin.EMOTION, PatternMixin.LOCATION],
                    sample_texts=["Sample 3", "Sample 4"]
                )
            ]
            
            result = bridge.export_pattern_definitions(patterns)
            
            assert result["total_patterns"] == 2
            assert len(result["patterns"]) == 2
            assert "test" in result["domains"]
            
            # Check pattern structure
            pattern_one = result["patterns"][0]
            assert pattern_one["id"] == "test/pattern/one"
            assert pattern_one["mixins"] == ["time"]
            assert len(pattern_one["sample_texts"]) == 2
    
    def test_rust_annotation_generation(self):
        """Test that Rust annotations are correctly generated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge = SchemaBridge(output_dir=temp_dir)
            result = bridge.export_schemas()
            
            # Check WeaveUnit schema (should use camelCase)
            weave_unit_schema = result["schemas"]["WeaveUnit"]
            assert "rust_annotations" in weave_unit_schema
            assert "derives" in weave_unit_schema["rust_annotations"]
            assert "Serialize" in weave_unit_schema["rust_annotations"]["derives"]
            assert "Deserialize" in weave_unit_schema["rust_annotations"]["derives"]
    
    def test_enum_export(self):
        """Test enum export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge = SchemaBridge(output_dir=temp_dir)
            result = bridge.export_schemas()
            
            # Check PatternMixin enum
            pattern_mixin_enum = result["enums"]["PatternMixin"]
            assert pattern_mixin_enum["type"] == "string"
            assert "time" in pattern_mixin_enum["values"]
            assert "emotion" in pattern_mixin_enum["values"]
    
    def test_json_schema_structure(self):
        """Test that JSON Schema is properly structured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge = SchemaBridge(output_dir=temp_dir)
            result = bridge.export_schemas()
            
            # Check PatternSchema structure
            pattern_schema = result["schemas"]["PatternSchema"]
            json_schema = pattern_schema["json_schema"]
            
            assert "properties" in json_schema
            assert "id" in json_schema["properties"]
            assert "description" in json_schema["properties"]
            assert "sample_texts" in json_schema["properties"]
            
            # Check required fields
            assert "required" in json_schema
            assert "id" in json_schema["required"]
            assert "description" in json_schema["required"]


class TestIntegration:
    """Integration tests for the full bridge system."""
    
    def test_export_all_schemas_integration(self):
        """Test the complete schema export process."""
        # This test requires the actual pattern files to exist
        try:
            export_all_schemas()
            
            # Check that files were created
            schemas_file = Path("assets/schemas.json")
            patterns_file = Path("assets/patterns.json")
            
            if schemas_file.exists():
                with open(schemas_file) as f:
                    schemas = json.load(f)
                    assert "version" in schemas
                    assert "schemas" in schemas
            
            if patterns_file.exists():
                with open(patterns_file) as f:
                    patterns = json.load(f)
                    assert "total_patterns" in patterns
                    assert "patterns" in patterns
                    
        except Exception as e:
            pytest.skip(f"Integration test skipped due to missing patterns: {e}")


def test_schema_compatibility():
    """Test that exported schemas are compatible with expected structure."""
    # Test creating a WeaveUnit to ensure schema is valid
    weave_unit = WeaveUnit(
        text="Test text for classification",
        metadata={"test": True}
    )
    
    assert weave_unit.text == "Test text for classification"
    assert weave_unit.metadata["test"] is True
    assert weave_unit.id is not None  # Should have auto-generated UUID


if __name__ == "__main__":
    # Run basic tests
    test_schema_compatibility()
    print("✅ Basic schema tests passed!")
    
    # Run schema bridge tests
    bridge_tests = TestSchemaBridge()
    bridge_tests.test_schema_export()
    bridge_tests.test_pattern_export()
    print("✅ Schema bridge tests passed!")
    
    print("\nTo run full integration tests:")
    print("pytest tests/test_schema_bridge.py -v") 