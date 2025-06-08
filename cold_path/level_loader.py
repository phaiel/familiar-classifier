"""
🏗️ Level Schema Loader
Follows the same pattern as pattern_loader.py but for hierarchy level schemas
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional
import logging
from .level_schemas import LevelSchema, HierarchyLevel

logger = logging.getLogger(__name__)

class LevelSchemaLoader:
    """Loads and manages level schema definitions - mirrors PatternLoader"""
    
    def __init__(self, level_schemas_dir: str = "cold_path/level_schemas"):
        self.level_schemas_dir = Path(level_schemas_dir)
        self._level_cache: Dict[str, LevelSchema] = {}
        self._levels_by_hierarchy: Dict[HierarchyLevel, List[LevelSchema]] = {}
        
    def load_all_levels(self) -> List[LevelSchema]:
        """Load all level schemas from YAML files"""
        levels = []
        
        if not self.level_schemas_dir.exists():
            logger.warning(f"Level schemas directory not found: {self.level_schemas_dir}")
            return levels
            
        yaml_files = list(self.level_schemas_dir.glob("*.yaml"))
        logger.info(f"Found {len(yaml_files)} level schema files")
        
        for yaml_file in yaml_files:
            level = self.load_level_file(yaml_file)
            if level:
                levels.append(level)
                self._level_cache[level.id] = level
                
                # Group by hierarchy level
                if level.level not in self._levels_by_hierarchy:
                    self._levels_by_hierarchy[level.level] = []
                self._levels_by_hierarchy[level.level].append(level)
        
        logger.info(f"Loaded {len(levels)} level schemas")
        return levels
    
    def load_level_file(self, file_path: Path) -> Optional[LevelSchema]:
        """Load a single level schema file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning(f"Empty level schema file: {file_path}")
                return None
            
            # Validate and create level schema
            level = LevelSchema(**data)
            logger.debug(f"Loaded level schema: {level.id}")
            return level
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading level schema {file_path}: {e}")
            return None
    
    def get_level_by_id(self, level_id: str) -> Optional[LevelSchema]:
        """Get a level schema by its ID"""
        return self._level_cache.get(level_id)
    
    def get_levels_by_hierarchy(self, hierarchy_level: HierarchyLevel) -> List[LevelSchema]:
        """Get all level schemas for a specific hierarchy level"""
        return self._levels_by_hierarchy.get(hierarchy_level, [])
    
    def get_candidate_levels(self, hierarchy_level: HierarchyLevel, parent_filter: Optional[str] = None) -> List[LevelSchema]:
        """Get candidate level schemas for classification at a specific hierarchy level"""
        candidates = self.get_levels_by_hierarchy(hierarchy_level)
        
        if parent_filter:
            # Filter by parent relationship
            candidates = [level for level in candidates if level.parent_id == parent_filter]
        
        return candidates
    
    def get_all_domains(self) -> List[str]:
        """Get all unique domain IDs"""
        domains = self.get_levels_by_hierarchy(HierarchyLevel.DOMAIN)
        return [domain.id for domain in domains] 