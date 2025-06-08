"""Schema definitions for pattern classification system."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4
from datetime import datetime, timedelta


class PatternMixin(str, Enum):
    """Available mixins for patterns."""
    TIME = "time"
    EMOTION = "emotion"
    LOCATION = "location"
    PERSON = "person"
    ACTIVITY = "activity"
    HEALTH = "health"
    DEVELOPMENT = "development"


class PatternSchema(BaseModel):
    """Schema for pattern definitions with 6-level hierarchy."""
    id: str = Field(..., description="Hierarchical pattern ID: domain/area/topic/theme/focus/form")
    description: str = Field(..., description="Human-readable description for embedding")
    mixins: List[PatternMixin] = Field(default_factory=list, description="Schema composition mixins")
    sample_texts: List[str] = Field(..., description="Example texts for training embeddings")
    
    # 6-Level Hierarchy (auto-extracted from ID)
    domain: Optional[str] = Field(None, description="Highest-level conceptual group (e.g. self_state, child_development)")
    area: Optional[str] = Field(None, description="Life zone or interaction type (e.g. sleep, feeding, play)")
    topic: Optional[str] = Field(None, description="Functional grouping (e.g. nap, breastfeeding, toddler_meltdown)")
    theme: Optional[str] = Field(None, description="Conceptual behavior cluster (e.g. crib_nap, midday_nap)")
    focus: Optional[str] = Field(None, description="Leaf-like structural subdivision (e.g. early_am, afternoon)")
    form: Optional[str] = Field(None, description="Final pattern node (e.g. single_entry, recurring)")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('id')
    def validate_id_format(cls, v: str) -> str:
        """Validate that ID follows 6-level hierarchical format."""
        if not v or '/' not in v:
            raise ValueError("Pattern ID must be hierarchical (minimum: domain/area)")
        
        parts = v.split('/')
        if len(parts) < 2:
            raise ValueError("Pattern ID must have at least domain/area levels")
        elif len(parts) > 6:
            raise ValueError("Pattern ID cannot exceed 6 levels: domain/area/topic/theme/focus/form")
        
        return v
    
    @validator('sample_texts')
    def validate_sample_texts(cls, v: List[str]) -> List[str]:
        """Ensure we have at least one sample text."""
        if not v:
            raise ValueError("At least one sample text is required")
        return v
    
    def extract_hierarchy(self) -> Dict[str, Optional[str]]:
        """Extract all hierarchy levels from ID."""
        parts = self.id.split('/')
        levels = ['domain', 'area', 'topic', 'theme', 'focus', 'form']
        
        hierarchy = {}
        for i, level in enumerate(levels):
            hierarchy[level] = parts[i] if i < len(parts) else None
            
        return hierarchy
    
    def __init__(self, **data):
        """Initialize and extract hierarchy levels from ID."""
        super().__init__(**data)
        hierarchy = self.extract_hierarchy()
        self.domain = hierarchy['domain']
        self.area = hierarchy['area'] 
        self.topic = hierarchy['topic']
        self.theme = hierarchy['theme']
        self.focus = hierarchy['focus']
        self.form = hierarchy['form']
    
    def get_depth(self) -> int:
        """Get the depth of this pattern's hierarchy."""
        return len([level for level in [self.domain, self.area, self.topic, self.theme, self.focus, self.form] if level is not None])
    
    def get_parent_id(self) -> Optional[str]:
        """Get the parent pattern ID (one level up)."""
        parts = self.id.split('/')
        if len(parts) <= 1:
            return None
        return '/'.join(parts[:-1])
    
    def is_temporal(self) -> bool:
        """Check if this pattern includes temporal markers."""
        temporal_markers = ['early_am', 'morning', 'midday', 'afternoon', 'evening', 'night', 'late_night']
        return any(marker in self.id.lower() for marker in temporal_markers)


class WeaveUnit(BaseModel):
    """Input unit for classification."""
    id: UUID = Field(default_factory=uuid4)
    text: str = Field(..., description="Text content to be classified")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = Field(None, description="ISO timestamp")
    
    @classmethod
    def new(cls, text: str) -> 'WeaveUnit':
        """Create a new WeaveUnit with generated ID and timestamp."""
        return cls(
            id=uuid4(), 
            text=text, 
            metadata={}, 
            timestamp=datetime.utcnow().isoformat()
        )
    
    def is_recent(self) -> bool:
        """Check if this WeaveUnit is recent (within last 24 hours)."""
        if self.timestamp:
            try:
                ts = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
                return datetime.utcnow() - ts < timedelta(hours=24)
            except ValueError:
                return False
        return False
    
    def text_length(self) -> int:
        """Get the length of the text content."""
        return len(self.text)


class PatternMatch(BaseModel):
    """Result of pattern classification."""
    pattern_id: str = Field(..., description="ID of matched pattern")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative matches")
    embedding_vector: Optional[List[float]] = Field(None, description="Input embedding vector")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def new(cls, pattern_id: str, confidence: float) -> 'PatternMatch':
        """Create a new pattern match."""
        return cls(
            pattern_id=pattern_id, 
            confidence=confidence, 
            alternatives=[], 
            embedding_vector=None, 
            metadata={}
        )
    
    def is_confident(self, threshold: float) -> bool:
        """Check if this match meets a confidence threshold."""
        return self.confidence >= threshold
    
    def get_domain(self) -> Optional[str]:
        """Get the domain from the pattern ID (first part before '/')."""
        parts = self.pattern_id.split('/')
        return parts[0] if len(parts) > 0 else None
    
    def get_hierarchy_level(self, level: str) -> Optional[str]:
        """Get a specific hierarchy level from the pattern ID."""
        parts = self.pattern_id.split('/')
        levels = ['domain', 'area', 'topic', 'theme', 'focus', 'form']
        if level in levels:
            idx = levels.index(level)
            return parts[idx] if idx < len(parts) else None
        return None


class ClassificationRequest(BaseModel):
    """Request for pattern classification."""
    weave_unit: WeaveUnit
    max_alternatives: int = Field(default=3, ge=1, le=10)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    filter_by_domain: Optional[str] = Field(None, description="Filter results by domain")
    
    @classmethod
    def new(cls, text: str) -> 'ClassificationRequest':
        """Create a simple classification request."""
        return cls(
            weave_unit=WeaveUnit.new(text), 
            max_alternatives=3, 
            confidence_threshold=0.5, 
            filter_by_domain=None
        )
    
    @classmethod
    def with_domain(cls, text: str, domain: str) -> 'ClassificationRequest':
        """Create a classification request with domain filtering."""
        return cls(
            weave_unit=WeaveUnit.new(text), 
            max_alternatives=3, 
            confidence_threshold=0.5, 
            filter_by_domain=domain
        )


class ClassificationResponse(BaseModel):
    """Response from pattern classification."""
    request_id: UUID = Field(default_factory=uuid4)
    match: Optional[PatternMatch] = Field(None, description="Best match if above threshold")
    alternatives: List[PatternMatch] = Field(default_factory=list)
    processing_time_ms: float = Field(..., description="Classification time in milliseconds")
    status: str = Field(default="success")
    error_message: Optional[str] = Field(None)

    @classmethod
    def success(cls, primary_match: Optional[PatternMatch], alternatives: List[PatternMatch], processing_time: float) -> 'ClassificationResponse':
        """Create a successful classification response."""
        return cls(
            match=primary_match,
            alternatives=alternatives,
            processing_time_ms=processing_time,
            status="success"
        )
    
    @classmethod  
    def error(cls, error_message: str, processing_time: float) -> 'ClassificationResponse':
        """Create an error classification response."""
        return cls(
            match=None,
            alternatives=[],
            processing_time_ms=processing_time,
            status="error",
            error_message=error_message
        )

    def is_success(self) -> bool:
        """Check if the classification was successful."""
        return self.status == "success"


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