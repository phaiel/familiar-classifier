"""
Cold Path Package for Familiar Pattern Classifier

This package contains the pattern management, schema validation, and indexing
components of the Familiar Pattern Classifier system.
"""

from .schemas import (
    PatternSchema, 
    PatternMixin, 
    WeaveUnit, 
    PatternMatch, 
    ClassificationRequest, 
    ClassificationResponse, 
    IndexBuildConfig
)

from .pattern_loader import PatternLoader

__version__ = "1.0.0"
__all__ = [
    "PatternSchema",
    "PatternMixin", 
    "WeaveUnit",
    "PatternMatch",
    "ClassificationRequest",
    "ClassificationResponse", 
    "IndexBuildConfig",
    "PatternLoader"
] 