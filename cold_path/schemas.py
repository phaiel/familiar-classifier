"""Schema definitions for pattern classification system."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class PatternMixin(str, Enum):
    """Available mixins for patterns."""
    TIME = "time"
    EMOTION = "emotion"
    THREAD_LINK = "thread_link"
    LOCATION = "location"
    PERSON = "person"
    ACTIVITY = "activity"
    HEALTH = "health"
    DEVELOPMENT = "development"


class PatternSchema(BaseModel):
    """Schema for pattern definitions."""
    id: str = Field(..., description="Hierarchical pattern ID (e.g., 'child_development/sleep/nap/crib/early_am')")
    description: str = Field(..., description="Human-readable description for embedding")
    mixins: List[PatternMixin] = Field(default_factory=list, description="Schema composition mixins")
    sample_texts: List[str] = Field(..., description="Example texts for training embeddings")
    domain: Optional[str] = Field(None, description="Top-level domain (extracted from id)")
    category: Optional[str] = Field(None, description="Category (extracted from id)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('id')
    def validate_id_format(cls, v: str) -> str:
        """Validate that ID follows hierarchical format."""
        if not v or '/' not in v:
            raise ValueError("Pattern ID must be hierarchical (e.g., 'domain/category/subcategory')")
        return v
    
    @validator('sample_texts')
    def validate_sample_texts(cls, v: List[str]) -> List[str]:
        """Ensure we have at least one sample text."""
        if not v:
            raise ValueError("At least one sample text is required")
        return v
    
    def __post_init__(self) -> None:
        """Extract domain and category from ID."""
        parts = self.id.split('/')
        if len(parts) >= 1:
            self.domain = parts[0]
        if len(parts) >= 2:
            self.category = parts[1]


class WeaveUnit(BaseModel):
    """Input unit for classification."""
    id: UUID = Field(default_factory=uuid4)
    text: str = Field(..., description="Text content to be classified")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = Field(None, description="ISO timestamp")


class PatternMatch(BaseModel):
    """Result of pattern classification."""
    pattern_id: str = Field(..., description="ID of matched pattern")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative matches")
    embedding_vector: Optional[List[float]] = Field(None, description="Input embedding vector")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClassificationRequest(BaseModel):
    """Request for pattern classification."""
    weave_unit: WeaveUnit
    max_alternatives: int = Field(default=3, ge=1, le=10)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    filter_by_domain: Optional[str] = Field(None, description="Filter results by domain")


class ClassificationResponse(BaseModel):
    """Response from pattern classification."""
    request_id: UUID = Field(default_factory=uuid4)
    match: Optional[PatternMatch] = Field(None, description="Best match if above threshold")
    alternatives: List[PatternMatch] = Field(default_factory=list)
    processing_time_ms: float = Field(..., description="Classification time in milliseconds")
    status: str = Field(default="success")
    error_message: Optional[str] = Field(None)


class IndexBuildConfig(BaseModel):
    """Configuration for building pattern index (database agnostic)."""
    model_name: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")
    vector_store_type: str = Field(default="in_memory", description="Vector store backend (in_memory, qdrant, etc)")
    host: str = Field(default="localhost", description="Vector store host (if applicable)")
    port: int = Field(default=3000, description="Vector store port (if applicable)")
    collection_name: str = Field(default="pattern_index", description="Collection/index name")
    vector_size: int = Field(default=384, description="Embedding vector size")
    patterns_dir: str = Field(default="cold_path/patterns", description="Directory containing pattern YAML files")
    batch_size: int = Field(default=100, description="Batch size for processing")
    overwrite_collection: bool = Field(default=False, description="Whether to overwrite existing collection") 