"""
🏗️ Level Schema Definitions
Follows the same pattern as PatternSchema but for hierarchy levels
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class HierarchyLevel(str, Enum):
    DOMAIN = "domain"
    AREA = "area" 
    TOPIC = "topic"
    THEME = "theme"
    FOCUS = "focus"
    FORM = "form"

class LevelSchema(BaseModel):
    """Schema for hierarchy level definitions - follows same pattern as PatternSchema"""
    id: str = Field(..., description="Unique identifier for this level")
    level: HierarchyLevel = Field(..., description="Which hierarchy level this represents")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Semantic description for embedding")
    examples: List[str] = Field(..., description="Example texts that classify to this level")
    parent_id: Optional[str] = Field(None, description="Parent level ID (for filtering)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('examples')
    def validate_examples(cls, v: List[str]) -> List[str]:
        """Ensure we have at least one example text."""
        if not v:
            raise ValueError("At least one example text is required")
        return v

    @validator('id')
    def validate_id_format(cls, v: str) -> str:
        """Validate that ID follows naming conventions."""
        if not v or not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Level ID must be alphanumeric with underscores/hyphens")
        return v

    def get_embedding_text(self) -> str:
        """Get combined text for embedding generation (same approach as patterns)"""
        return f"{self.description} {' '.join(self.examples)}" 