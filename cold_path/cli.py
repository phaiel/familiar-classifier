"""CLI interface for pattern classification system."""

import typer
import json
import yaml
from uuid import uuid4
from pathlib import Path
from .schemas import (
    PatternSchema, WeaveUnit, PatternMatch, ClassificationRequest, 
    ClassificationResponse, IndexBuildConfig, PatternMixin
)
from .pattern_loader import PatternLoader
from .tools.build_pattern_index import PatternIndexBuilder

app = typer.Typer(help="🧠 Pattern Classifier - Cold Path CLI")


def get_all_pydantic_models():
    """Get all Pydantic models from our schema definitions"""
    models = {}
    
    # Core models from schemas.py
    models['PatternSchema'] = PatternSchema
    models['WeaveUnit'] = WeaveUnit
    models['PatternMatch'] = PatternMatch
    models['ClassificationRequest'] = ClassificationRequest
    models['ClassificationResponse'] = ClassificationResponse
    models['IndexBuildConfig'] = IndexBuildConfig
    
    # Enums
    models['PatternMixin'] = PatternMixin
    
    return models


@app.command()
def schema_dump(output_path: str = "assets/schemas.json"):
    """Export actual Pydantic schemas as JSON for the hot path."""
    models = get_all_pydantic_models()
    
    # Generate schemas directly (no complex cleaning)
    schemas = {}
    
    for name, model in models.items():
        try:
            if hasattr(model, 'model_json_schema'):
                # Pydantic v2 style 
                schemas[name] = model.model_json_schema()
            elif hasattr(model, 'schema'):
                # Pydantic v1 style fallback
                schemas[name] = model.schema()
            else:
                # For enums
                if hasattr(model, '__members__'):
                    schemas[name] = {
                        "type": "string",
                        "enum": [item.value for item in model],
                        "description": f"<enum '{name}'>"
                    }
                else:
                    schemas[name] = {
                        "type": "string",
                        "description": str(model)
                    }
        except Exception as e:
            print(f"⚠️  Could not generate schema for {name}: {e}")
            schemas[name] = {"error": str(e)}
    
    # Create output directory if it doesn't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write schemas with metadata (simple structure like ECS Familiar)
    output = {
        "schema_version": "1.0.0",
        "generated_by": "pattern-classifier-cold-path",
        "models": schemas
    }
    
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"✅ Real Pydantic schemas exported to {output_path}")
    print(f"📊 Exported {len(schemas)} model schemas:")
    for name in sorted(schemas.keys()):
        print(f"   • {name}")


@app.command()
def schema_summary():
    """Show a summary of all available schemas."""
    models = get_all_pydantic_models()
    
    print(f"📋 Available Pydantic Models ({len(models)} total):\n")
    
    for name, model in sorted(models.items()):
        try:
            if hasattr(model, 'model_fields'):
                # Pydantic v2
                field_count = len(model.model_fields)
                fields = list(model.model_fields.keys())[:3]  # Show first 3 fields
            elif hasattr(model, '__fields__'):
                # Pydantic v1 fallback  
                field_count = len(model.__fields__)
                fields = list(model.__fields__.keys())[:3]
            elif hasattr(model, '__members__'):
                # Enum
                field_count = len(model.__members__)
                fields = list(model.__members__.keys())[:3]
                print(f"  🔹 {name} (Enum)")
                print(f"     Values ({field_count}): {', '.join(fields)}")
                if field_count > 3:
                    print(f"     ... (+{field_count - 3} more)")
                print()
                continue
            else:
                field_count = 0
                fields = []
            
            field_preview = ", ".join(fields)
            if field_count > 3:
                field_preview += f", ... (+{field_count - 3} more)"
            
            print(f"  🔹 {name}")
            print(f"     Fields ({field_count}): {field_preview}")
            
            if hasattr(model, '__doc__') and model.__doc__:
                doc = model.__doc__.strip().split('\n')[0]  # First line only
                print(f"     Doc: {doc}")
            print()
            
        except Exception as e:
            print(f"  ❌ {name}: Error reading model ({e})")


@app.command()
def weave_generate():
    """Generates and prints a sample WeaveUnit as JSON."""
    weave = WeaveUnit(
        text="He napped in his crib early this morning"
    )
    print("--- Sample WeaveUnit ---")
    print(weave.model_dump_json(indent=2))


@app.command()
def patterns_validate(patterns_dir: str = "cold_path/patterns"):
    """Validates all pattern YAML files against the PatternSchema."""
    try:
        loader = PatternLoader(patterns_dir)
        patterns = loader.load_all_patterns()
        print(f"✅ All {len(patterns)} patterns in {patterns_dir} are valid:")
        
        domains = {}
        for pattern in patterns:
            domain = getattr(pattern, 'domain', None) or "unknown"
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(pattern.id)
        
        for domain, pattern_ids in domains.items():
            print(f"  📁 {domain}: {len(pattern_ids)} patterns")
            for pid in pattern_ids[:3]:  # Show first 3
                print(f"     • {pid}")
            if len(pattern_ids) > 3:
                print(f"     ... (+{len(pattern_ids) - 3} more)")
            
    except Exception as e:
        print(f"❌ Pattern validation failed: {e}")


@app.command()
def index_build(
    patterns_dir: str = typer.Option("cold_path/patterns", "--patterns-dir", help="Patterns directory"),
    vector_store: str = typer.Option("in_memory", "--vector-store", help="Vector store type (in_memory, qdrant)"),
    host: str = typer.Option("localhost", "--host", help="Vector store host"),
    port: int = typer.Option(3000, "--port", help="Vector store port"),
    collection_name: str = typer.Option("pattern_index", "--collection", help="Collection name"),
    model_name: str = typer.Option("all-MiniLM-L6-v2", "--model", help="Embedding model"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing collection"),
):
    """Build vector index for patterns (database agnostic)."""
    import asyncio
    
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
    
    async def run_build():
        try:
            builder = PatternIndexBuilder(config)
            result = await builder.build_index()
            
            if result["status"] == "success":
                print("🎉 Index built successfully!")
                print(f"📊 Patterns indexed: {result['patterns_indexed']}")
                print(f"🏗️  Vector store: {result['vector_store_type']}")
                print(f"⏱️  Build time: {result['build_time_seconds']}s")
                print(f"🌐 URL: {result['vector_store_url']}")
                
                if result.get("upload_result"):
                    upload = result["upload_result"]
                    print(f"📤 Upload: {upload.get('message', 'Success')}")
                    
            else:
                print(f"❌ Build failed: {result['message']}")
                raise typer.Exit(1)
                
        except Exception as e:
            print(f"❌ Error building index: {e}")
            raise typer.Exit(1)
    
    asyncio.run(run_build())


if __name__ == "__main__":
    app() 