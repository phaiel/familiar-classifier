"""Build pattern vector index using MiniLM embeddings (database agnostic)."""

import asyncio
from typing import Dict, List
import numpy as np
from rich.console import Console
from rich.progress import Progress, TaskID
from sentence_transformers import SentenceTransformer
from loguru import logger

from ..pattern_loader import PatternLoader
from ..schemas import PatternSchema, IndexBuildConfig
from ..vector_stores import create_vector_store


class PatternIndexBuilder:
    """Builds pattern vector index using any vector store backend."""
    
    def __init__(self, config: IndexBuildConfig):
        self.config = config
        self.console = Console()
        self.model = None
        self.vector_store = None
        
    async def build_index(self) -> Dict:
        """Build the complete pattern index."""
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Load patterns
            self.console.print("[bold blue]Loading patterns...[/bold blue]")
            patterns = self._load_patterns()
            
            # Generate embeddings
            self.console.print("[bold blue]Generating embeddings...[/bold blue]")
            embeddings = self._generate_embeddings(patterns)
            
            # Initialize vector store
            self.console.print(f"[bold blue]Initializing {self.config.vector_store_type} vector store...[/bold blue]")
            await self._setup_vector_store()
            
            # Upload patterns
            self.console.print(f"[bold blue]Uploading to {self.config.vector_store_type}...[/bold blue]")
            upload_result = await self.vector_store.upload_patterns(patterns, embeddings)
            
            end_time = asyncio.get_event_loop().time()
            build_time = end_time - start_time
            
            # Get final stats
            stats = await self.vector_store.get_stats()
            
            return {
                "status": "success",
                "patterns_indexed": len(patterns),
                "domains": list(set(p.domain for p in patterns if p.domain)),
                "build_time_seconds": round(build_time, 2),
                "vector_store_type": self.config.vector_store_type,
                "vector_store_url": f"{self.config.host}:{self.config.port}",
                "upload_result": upload_result,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Index build failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _load_patterns(self) -> List[PatternSchema]:
        """Load all pattern definitions."""
        loader = PatternLoader(self.config.patterns_dir)
        patterns = loader.load_all_patterns()
        
        if not patterns:
            raise ValueError(f"No patterns found in {self.config.patterns_dir}")
        
        logger.info(f"Loaded {len(patterns)} patterns")
        
        # Group by domain for stats
        domains = {}
        for pattern in patterns:
            domain = pattern.domain or "unknown"
            domains[domain] = domains.get(domain, 0) + 1
        
        self.console.print(f"📊 Patterns by domain: {domains}")
        return patterns
    
    def _generate_embeddings(self, patterns: List[PatternSchema]) -> Dict[str, np.ndarray]:
        """Generate embeddings for all patterns."""
        if not self.model:
            logger.info(f"Loading model: {self.config.model_name}")
            self.model = SentenceTransformer(self.config.model_name)
        
        embeddings = {}
        
        with Progress() as progress:
            task = progress.add_task("Generating embeddings...", total=len(patterns))
            
            for pattern in patterns:
                # Use the first sample text for embedding (could be enhanced to use all)
                text = pattern.sample_texts[0] if pattern.sample_texts else pattern.description
                
                # Generate embedding
                embedding = self.model.encode(text, convert_to_numpy=True)
                embeddings[pattern.id] = embedding
                
                progress.update(task, advance=1)
        
        logger.info(f"Generated embeddings for {len(embeddings)} patterns")
        logger.info(f"Embedding dimension: {len(next(iter(embeddings.values())))}")
        
        return embeddings
    
    async def _setup_vector_store(self) -> None:
        """Initialize and setup the vector store."""
        self.vector_store = create_vector_store(
            vector_store_type=self.config.vector_store_type,
            host=self.config.host,
            port=self.config.port
        )
        
        # Create collection
        await self.vector_store.create_collection(
            collection_name=self.config.collection_name,
            vector_size=self.config.vector_size,
            overwrite=self.config.overwrite_collection
        )
        
        # Health check
        is_healthy = await self.vector_store.health_check()
        if not is_healthy:
            raise RuntimeError(f"Vector store health check failed")
        
        logger.info(f"✅ Vector store {self.config.vector_store_type} is ready")


# CLI interface (optional, can be used standalone)
def main():
    """CLI entry point for building index."""
    import typer
    
    def build_index(
        patterns_dir: str = typer.Option("cold_path/patterns", "--patterns-dir", help="Patterns directory"),
        vector_store: str = typer.Option("in_memory", "--vector-store", help="Vector store type (in_memory, qdrant)"),
        host: str = typer.Option("localhost", "--host", help="Vector store host"),
        port: int = typer.Option(3000, "--port", help="Vector store port"),
        collection_name: str = typer.Option("pattern_index", "--collection", help="Collection name"),
        model_name: str = typer.Option("all-MiniLM-L6-v2", "--model", help="Embedding model"),
        overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing collection"),
    ):
        """Build pattern vector index."""
        
        # Adjust default port based on vector store type
        if vector_store == "qdrant" and port == 3000:
            port = 6333
        
        config = IndexBuildConfig(
            patterns_dir=patterns_dir,
            vector_store_type=vector_store,
            host=host,
            port=port,
            collection_name=collection_name,
            model_name=model_name,
            overwrite_collection=overwrite,
        )
        
        console = Console()
        
        async def run_build():
            builder = PatternIndexBuilder(config)
            result = await builder.build_index()
            
            if result["status"] == "success":
                console.print("[bold green]✅ Index built successfully![/bold green]")
                console.print(f"📊 Patterns indexed: {result['patterns_indexed']}")
                console.print(f"🏗️  Vector store: {result['vector_store_type']}")
                console.print(f"⏱️  Build time: {result['build_time_seconds']}s")
                console.print(f"🌐 URL: {result['vector_store_url']}")
            else:
                console.print(f"[bold red]❌ Build failed: {result['message']}[/bold red]")
                raise typer.Exit(1)
        
        asyncio.run(run_build())
    
    app = typer.Typer()
    app.command()(build_index)
    app()


if __name__ == "__main__":
    main() 