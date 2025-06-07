"""Pattern loader for reading and validating YAML pattern definitions."""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Any
import logging

from .schemas import PatternSchema

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PatternLoader:
    """Loads and validates pattern definitions from YAML files."""
    
    def __init__(self, patterns_dir: str = "cold_path/patterns"):
        self.patterns_dir = Path(patterns_dir)
        self._patterns_cache: Dict[str, PatternSchema] = {}
    
    def load_all_patterns(self) -> List[PatternSchema]:
        """Load all pattern definitions from the patterns directory."""
        patterns = []
        
        if not self.patterns_dir.exists():
            logger.warning(f"Patterns directory {self.patterns_dir} does not exist")
            return patterns
        
        # Find all YAML files recursively
        yaml_files = list(self.patterns_dir.rglob("*.yaml")) + list(self.patterns_dir.rglob("*.yml"))
        
        logger.info(f"Found {len(yaml_files)} pattern files")
        
        for yaml_file in yaml_files:
            try:
                pattern = self.load_pattern_file(yaml_file)
                if pattern:
                    patterns.append(pattern)
                    self._patterns_cache[pattern.id] = pattern
            except Exception as e:
                logger.error(f"Failed to load pattern from {yaml_file}: {e}")
                continue
        
        logger.info(f"Successfully loaded {len(patterns)} patterns")
        return patterns
    
    def load_pattern_file(self, file_path: Path) -> PatternSchema | None:
        """Load a single pattern file and validate it."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning(f"Empty pattern file: {file_path}")
                return None
            
            # Validate and create pattern schema
            pattern = PatternSchema(**data)
            
            # Extract domain and category from ID if not set
            if not pattern.domain or not pattern.category:
                parts = pattern.id.split('/')
                if len(parts) >= 1:
                    pattern.domain = parts[0]
                if len(parts) >= 2:
                    pattern.category = parts[1]
            
            logger.debug(f"Loaded pattern: {pattern.id}")
            return pattern
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading pattern {file_path}: {e}")
            return None
    
    def get_pattern_by_id(self, pattern_id: str) -> PatternSchema | None:
        """Get a pattern by its ID."""
        if pattern_id in self._patterns_cache:
            return self._patterns_cache[pattern_id]
        
        # If not cached, try to find and load it
        expected_path = self.patterns_dir / (pattern_id.replace('/', os.sep) + '.yaml')
        if expected_path.exists():
            return self.load_pattern_file(expected_path)
        
        return None
    
    def get_patterns_by_domain(self, domain: str) -> List[PatternSchema]:
        """Get all patterns for a specific domain."""
        return [p for p in self._patterns_cache.values() if p.domain == domain]
    
    def get_all_domains(self) -> List[str]:
        """Get all unique domains."""
        return list(set(p.domain for p in self._patterns_cache.values() if p.domain))
    
    def validate_patterns(self) -> Dict[str, Any]:
        """Validate all patterns and return statistics."""
        stats = {
            "total_patterns": len(self._patterns_cache),
            "domains": {},
            "validation_errors": [],
            "patterns_by_domain": {}
        }
        
        for pattern in self._patterns_cache.values():
            # Count by domain
            domain = pattern.domain or "unknown"
            if domain not in stats["domains"]:
                stats["domains"][domain] = 0
                stats["patterns_by_domain"][domain] = []
            
            stats["domains"][domain] += 1
            stats["patterns_by_domain"][domain].append(pattern.id)
            
            # Validate pattern quality
            if len(pattern.sample_texts) < 3:
                stats["validation_errors"].append(
                    f"Pattern {pattern.id} has only {len(pattern.sample_texts)} sample texts (recommended: 3+)"
                )
            
            if len(pattern.description) < 10:
                stats["validation_errors"].append(
                    f"Pattern {pattern.id} has very short description"
                )
        
        return stats 