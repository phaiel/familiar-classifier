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


@app.command()
def temporal_analysis(
    patterns_dir: str = typer.Option("cold_path/patterns", "--patterns-dir", help="Directory containing pattern YAML files"),
    test_patterns_dir: str = typer.Option("test_patterns", "--test-patterns-dir", help="Directory containing test patterns")
):
    """Analyze temporal patterns and provide hierarchy recommendations."""
    try:
        print("🕒 Temporal Pattern Analysis")
        print("=" * 50)
        
        # Load all patterns
        all_patterns = []
        for dir_path in [patterns_dir, test_patterns_dir]:
            if Path(dir_path).exists():
                try:
                    loader = PatternLoader(dir_path)
                    patterns = loader.load_all_patterns()
                    all_patterns.extend(patterns)
                    print(f"📁 Loaded {len(patterns)} patterns from {dir_path}")
                except Exception as e:
                    print(f"⚠️  Could not load patterns from {dir_path}: {e}")
        
        if not all_patterns:
            print("❌ No patterns found to analyze")
            return
        
        # Analyze temporal markers
        temporal_patterns = []
        non_temporal_patterns = []
        
        temporal_markers = ['early_am', 'morning', 'midday', 'afternoon', 'evening', 'night', 'late_night']
        
        for pattern in all_patterns:
            has_temporal = any(marker in pattern.id.lower() for marker in temporal_markers)
            if has_temporal:
                temporal_patterns.append(pattern)
            else:
                non_temporal_patterns.append(pattern)
        
        # Analysis Results
        print(f"\n📊 Analysis Results:")
        print(f"   Total Patterns: {len(all_patterns)}")
        print(f"   With Temporal Markers: {len(temporal_patterns)} ({len(temporal_patterns)/len(all_patterns)*100:.1f}%)")
        print(f"   Without Temporal Markers: {len(non_temporal_patterns)} ({len(non_temporal_patterns)/len(all_patterns)*100:.1f}%)")
        
        # Show temporal conflicts
        if len(temporal_patterns) >= 2:
            print(f"\n🔍 Temporal Conflict Analysis:")
            
            # Group by base pattern (without temporal marker)
            base_patterns = {}
            for pattern in temporal_patterns:
                parts = pattern.id.split('/')
                if len(parts) >= 5:  # Has focus level
                    base_id = '/'.join(parts[:-2])  # Remove focus and form
                    if base_id not in base_patterns:
                        base_patterns[base_id] = []
                    base_patterns[base_id].append(pattern)
            
            conflicts_found = False
            for base_id, patterns in base_patterns.items():
                if len(patterns) > 1:
                    conflicts_found = True
                    temporal_variants = []
                    for p in patterns:
                        parts = p.id.split('/')
                        if len(parts) >= 5:
                            temporal_variants.append(parts[-2])  # Focus level
                    print(f"   📋 {base_id}")
                    print(f"      Temporal variants: {', '.join(temporal_variants)}")
                    print(f"      ⚠️  Without temporal markers, these would collide!")
            
            if not conflicts_found:
                print("   ✅ No temporal conflicts detected")
        
        # Hierarchy depth analysis
        print(f"\n📏 Hierarchy Depth Analysis:")
        
        depth_counts = {}
        depth_examples = {}
        
        for pattern in all_patterns:
            parts = pattern.id.split('/')
            depth = len(parts)
            if depth not in depth_counts:
                depth_counts[depth] = 0
                depth_examples[depth] = []
            depth_counts[depth] += 1
            if len(depth_examples[depth]) < 2:
                depth_examples[depth].append(pattern.id)
        
        for depth in sorted(depth_counts.keys()):
            examples = ", ".join(depth_examples[depth])
            if len(depth_examples[depth]) > 1:
                examples += f" (and {depth_counts[depth] - len(depth_examples[depth])} more)"
            print(f"   Depth {depth}: {depth_counts[depth]} patterns - {examples}")
        
        # Show 6-level hierarchy mapping
        print(f"\n🏗️  6-Level Hierarchy Mapping:")
        levels = ['Domain', 'Area', 'Topic', 'Theme', 'Focus', 'Form']
        descriptions = [
            'Highest-level conceptual group',
            'Life zone or interaction type', 
            'Functional grouping',
            'Conceptual behavior cluster',
            'Leaf-like structural subdivision',
            'Final pattern node'
        ]
        
        for i, (level, desc) in enumerate(zip(levels, descriptions), 1):
            print(f"   {i}. {level:<8} - {desc}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if len(temporal_patterns) / len(all_patterns) < 0.7:
            print("   🚨 Consider adding temporal markers to more patterns")
            print("      Temporal context prevents classification ambiguity")
        
        print("   ✅ Include temporal markers when:")
        print("      - Same activity occurs at different times with different characteristics")
        print("      - Time of day affects behavior/success patterns") 
        print("      - Context matters for intervention strategies")
        
        print("   ⚖️  Omit temporal markers when:")
        print("      - Pattern is time-agnostic")
        print("      - Temporal variation is not behaviorally significant")
        
        # Final recommendation
        optimal_depth = 5 if len(temporal_patterns) > 0 else 4
        print(f"\n🎯 Optimal depth for this dataset: {optimal_depth} levels")
        print(f"   Includes temporal markers: {'Yes' if optimal_depth == 5 else 'No'}")
        
        # Show sample 6-level pattern
        print(f"\n📝 Sample 6-Level Pattern Structure:")
        print("   self_state/emotional_regulation/overwhelm/sensory_overload/evening/shutdown_response")
        print("   ↳ Domain/Area/Topic/Theme/Focus/Form")
        
    except Exception as e:
        print(f"❌ Error in temporal analysis: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app() 