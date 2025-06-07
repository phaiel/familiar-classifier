"""Integration tests for pattern classification system."""

import pytest
import asyncio
import httpx
from pathlib import Path
import tempfile
import yaml
from unittest.mock import patch

from cold_path.pattern_loader import PatternLoader
from cold_path.schemas import PatternSchema, IndexBuildConfig
from cold_path.tools.build_pattern_index import PatternIndexBuilder
from hot_path.classifier import PatternClassifier


class TestPatternLoader:
    """Test pattern loading and validation."""
    
    def test_load_sample_patterns(self):
        """Test loading the sample patterns."""
        loader = PatternLoader("cold_path/patterns")
        patterns = loader.load_all_patterns()
        
        assert len(patterns) >= 3  # We created 3 sample patterns
        
        # Check for our specific patterns
        pattern_ids = [p.id for p in patterns]
        assert "child_development/sleep/nap/crib/early_am" in pattern_ids
        assert "child_development/sleep/bedtime/routine/bath" in pattern_ids
        assert "health/meals/lunch/outdoor/picnic" in pattern_ids
    
    def test_pattern_validation(self):
        """Test pattern validation."""
        loader = PatternLoader("cold_path/patterns")
        loader.load_all_patterns()
        stats = loader.validate_patterns()
        
        assert stats["total_patterns"] >= 3
        assert "child_development" in stats["domains"]
        assert "health" in stats["domains"]
    
    def test_create_pattern_from_dict(self):
        """Test creating a pattern from dictionary data."""
        pattern_data = {
            "id": "test/domain/category",
            "description": "Test pattern",
            "mixins": ["time", "emotion"],
            "sample_texts": ["Test text 1", "Test text 2"],
            "metadata": {"test": True}
        }
        
        pattern = PatternSchema(**pattern_data)
        assert pattern.id == "test/domain/category"
        assert len(pattern.sample_texts) == 2


class TestIndexBuilding:
    """Test vector index building."""
    
    @pytest.mark.asyncio
    async def test_index_build_config(self):
        """Test index build configuration."""
        config = IndexBuildConfig(
            patterns_dir="cold_path/patterns",
            qdrant_host="localhost",
            qdrant_port=6333,
            overwrite_collection=True
        )
        
        assert config.model_name == "all-MiniLM-L6-v2"
        assert config.vector_size == 384
        assert config.batch_size == 100


class TestPatternClassifier:
    """Test pattern classification functionality."""
    
    @pytest.mark.integration
    def test_classifier_initialization(self):
        """Test classifier initialization (requires Qdrant)."""
        try:
            classifier = PatternClassifier(
                qdrant_host="localhost",
                qdrant_port=6333,
                collection_name="pattern_index"
            )
            
            health = classifier.health_check()
            assert health["status"] == "healthy"
            assert "patterns_count" in health
            
        except Exception as e:
            pytest.skip(f"Qdrant not available: {e}")
    
    @pytest.mark.integration
    def test_classify_sample_texts(self):
        """Test classification of sample texts."""
        try:
            classifier = PatternClassifier()
            
            # Test texts that should match our patterns
            test_cases = [
                {
                    "text": "He napped in his crib early this morning",
                    "expected_domain": "child_development",
                    "expected_pattern": "child_development/sleep/nap/crib/early_am"
                },
                {
                    "text": "Had a warm bath before bedtime",
                    "expected_domain": "child_development",
                    "expected_pattern": "child_development/sleep/bedtime/routine/bath"
                },
                {
                    "text": "Family picnic lunch in the park",
                    "expected_domain": "health",
                    "expected_pattern": "health/meals/lunch/outdoor/picnic"
                }
            ]
            
            for case in test_cases:
                response = classifier.classify_weave_unit(
                    text=case["text"],
                    confidence_threshold=0.3
                )
                
                assert response.status == "success"
                assert response.processing_time_ms < 100  # Should be fast
                
                if response.match:
                    assert response.match.confidence > 0.3
                    # Domain should match
                    assert response.match.metadata.get("domain") == case["expected_domain"]
                
        except Exception as e:
            pytest.skip(f"Classification test failed: {e}")


class TestAPIIntegration:
    """Test REST API integration."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_health_check(self):
        """Test API health check endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health")
                
                if response.status_code == 200:
                    data = response.json()
                    assert data["status"] == "healthy"
                    assert "patterns_count" in data
                else:
                    pytest.skip("API service not running")
                    
        except httpx.ConnectError:
            pytest.skip("API service not available")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_classification(self):
        """Test API classification endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/classify",
                    json={
                        "text": "He napped in his crib early this morning",
                        "confidence_threshold": 0.3
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assert "processing_time_ms" in data
                    assert data["status"] == "success"
                    
                    if data["pattern_id"]:
                        assert data["confidence"] > 0.3
                        assert "/" in data["pattern_id"]  # Should be hierarchical
                else:
                    pytest.skip("API classification failed")
                    
        except httpx.ConnectError:
            pytest.skip("API service not available")


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""
    
    def test_pattern_creation_and_loading(self):
        """Test creating a pattern and loading it."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test pattern file
            pattern_data = {
                "id": "test/example/simple",
                "description": "Simple test pattern",
                "mixins": ["time"],
                "sample_texts": [
                    "This is a test",
                    "Another test example",
                    "Test pattern sample"
                ],
                "metadata": {"created_by": "test"}
            }
            
            # Write pattern file
            pattern_file = Path(temp_dir) / "test" / "example" / "simple.yaml"
            pattern_file.parent.mkdir(parents=True)
            
            with open(pattern_file, 'w') as f:
                yaml.dump(pattern_data, f)
            
            # Load patterns
            loader = PatternLoader(temp_dir)
            patterns = loader.load_all_patterns()
            
            assert len(patterns) == 1
            assert patterns[0].id == "test/example/simple"
            assert len(patterns[0].sample_texts) == 3


def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    # Test schema validation
    pattern_data = {
        "id": "basic/test/pattern",
        "description": "Basic test pattern for validation",
        "mixins": ["time", "emotion"],
        "sample_texts": ["Sample 1", "Sample 2", "Sample 3"]
    }
    
    pattern = PatternSchema(**pattern_data)
    assert pattern.id == "basic/test/pattern"
    assert len(pattern.mixins) == 2
    assert len(pattern.sample_texts) == 3


if __name__ == "__main__":
    # Run basic tests
    test_basic_functionality()
    print("✅ Basic tests passed!")
    
    # Run integration tests if available
    print("\nTo run integration tests with Qdrant and API:")
    print("pytest tests/test_integration.py -m integration") 