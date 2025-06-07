"""Database agnostic vector store interfaces and implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import json
import requests
import logging

from .schemas import PatternSchema

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def create_collection(self, collection_name: str, vector_size: int, overwrite: bool = False) -> None:
        """Create a collection/index."""
        pass
    
    @abstractmethod
    async def upload_patterns(self, patterns: List[PatternSchema], embeddings: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Upload patterns and their embeddings."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the vector store is healthy."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        pass


class InMemoryVectorStore(VectorStore):
    """In-memory vector store implementation (sends to Rust hot path)."""
    
    def __init__(self, host: str = "localhost", port: int = 3000):
        self.base_url = f"http://{host}:{port}"
        
    async def create_collection(self, collection_name: str, vector_size: int, overwrite: bool = False) -> None:
        """Create collection (for in-memory store, this is mostly a no-op)."""
        logger.info(f"🧠 Using in-memory vector store at {self.base_url}")
        
        # Check if the service is running
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Hot path service is running")
            else:
                logger.warning(f"⚠️  Hot path service returned status {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"❌ Could not connect to hot path service: {e}")
            raise RuntimeError(f"Hot path service not available at {self.base_url}")
    
    async def upload_patterns(self, patterns: List[PatternSchema], embeddings: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Upload patterns to the hot path service."""
        logger.info(f"📤 Sending {len(patterns)} patterns to hot path service")
        
        # For in-memory store, we can either:
        # 1. Send patterns via API to the hot path (if it has an upload endpoint)
        # 2. Save patterns to a file that hot path can load
        # 3. For now, just save to a JSON file for hot path to consume
        
        patterns_data = []
        for pattern in patterns:
            if pattern.id in embeddings:
                pattern_data = {
                    "id": pattern.id,
                    "description": pattern.description,
                    "domain": pattern.domain,
                    "sample_texts": pattern.sample_texts,
                    "metadata": pattern.metadata,
                    "embedding": embeddings[pattern.id].tolist()  # Convert numpy to list
                }
                patterns_data.append(pattern_data)
        
        # Save to assets directory for hot path to consume
        import os
        os.makedirs("assets", exist_ok=True)
        
        with open("assets/patterns_with_embeddings.json", "w") as f:
            json.dump(patterns_data, f, indent=2)
        
        logger.info(f"✅ Saved {len(patterns_data)} patterns to assets/patterns_with_embeddings.json")
        logger.info("🔄 Hot path can load this file on startup")
        
        return {
            "status": "success",
            "patterns_saved": len(patterns_data),
            "file_path": "assets/patterns_with_embeddings.json",
            "message": "Patterns saved for hot path to consume"
        }
    
    async def health_check(self) -> bool:
        """Check if the in-memory vector store (hot path) is healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics from hot path."""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status code {response.status_code}"}
        except requests.RequestException as e:
            return {"error": str(e)}


class QdrantVectorStore(VectorStore):
    """Qdrant vector store implementation (optional, for compatibility)."""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.host = host
        self.port = port
        self._client = None
    
    @property
    def client(self):
        """Lazy loading of Qdrant client (only if actually used)."""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(host=self.host, port=self.port)
            except ImportError:
                raise ImportError("qdrant-client not installed. Install with: pip install qdrant-client")
        return self._client
    
    async def create_collection(self, collection_name: str, vector_size: int, overwrite: bool = False) -> None:
        """Create Qdrant collection."""
        try:
            from qdrant_client.http.models import Distance, VectorParams
        except ImportError:
            raise ImportError("qdrant-client not installed. Install with: pip install qdrant-client")
        
        # Check if collection exists
        collections = self.client.get_collections()
        collection_exists = any(c.name == collection_name for c in collections.collections)
        
        if collection_exists and overwrite:
            logger.info(f"🗑️  Deleting existing collection: {collection_name}")
            self.client.delete_collection(collection_name)
        elif collection_exists and not overwrite:
            logger.info(f"📊 Collection '{collection_name}' already exists")
            return
        
        logger.info(f"🏗️  Creating collection: {collection_name}")
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
    
    async def upload_patterns(self, patterns: List[PatternSchema], embeddings: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Upload patterns to Qdrant."""
        try:
            from qdrant_client.http.models import PointStruct
        except ImportError:
            raise ImportError("qdrant-client not installed. Install with: pip install qdrant-client")
        
        points = []
        for pattern in patterns:
            if pattern.id in embeddings:
                point = PointStruct(
                    id=len(points),
                    vector=embeddings[pattern.id].tolist(),
                    payload={
                        "pattern_id": pattern.id,
                        "description": pattern.description,
                        "domain": pattern.domain,
                        "sample_texts": pattern.sample_texts,
                        "metadata": pattern.metadata,
                    },
                )
                points.append(point)
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(collection_name="patterns", points=batch)
        
        return {
            "status": "success",
            "patterns_uploaded": len(points),
            "message": f"Uploaded to Qdrant at {self.host}:{self.port}"
        }
    
    async def health_check(self) -> bool:
        """Check Qdrant health."""
        try:
            collections = self.client.get_collections()
            return True
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Qdrant statistics."""
        try:
            collections = self.client.get_collections()
            return {
                "type": "qdrant",
                "host": self.host,
                "port": self.port,
                "collections": [c.name for c in collections.collections],
            }
        except Exception as e:
            return {"error": str(e)}


def create_vector_store(vector_store_type: str, host: str, port: int) -> VectorStore:
    """Factory function to create vector store instances."""
    if vector_store_type.lower() == "in_memory":
        return InMemoryVectorStore(host=host, port=port)
    elif vector_store_type.lower() == "qdrant":
        return QdrantVectorStore(host=host, port=port)
    else:
        raise ValueError(f"Unknown vector store type: {vector_store_type}. Supported: in_memory, qdrant") 