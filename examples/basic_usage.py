#!/usr/bin/env python3
"""Basic usage examples for the pattern classification service."""

import asyncio
import httpx
from typing import List, Dict, Any

# Classification service URL
SERVICE_URL = "http://localhost:8000"


async def classify_text(text: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
    """Classify a single text using the REST API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVICE_URL}/classify",
            json={
                "text": text,
                "confidence_threshold": confidence_threshold,
                "max_alternatives": 3
            }
        )
        response.raise_for_status()
        return response.json()


async def classify_batch(texts: List[str]) -> Dict[str, Any]:
    """Classify multiple texts in batch."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVICE_URL}/classify/batch",
            json=texts
        )
        response.raise_for_status()
        return response.json()


async def get_service_stats() -> Dict[str, Any]:
    """Get service performance statistics."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICE_URL}/stats")
        response.raise_for_status()
        return response.json()


async def main():
    """Run examples."""
    print("🧠 Familiar Pattern Classification - Basic Usage Examples")
    print("=" * 60)
    
    # Test texts
    test_texts = [
        "He napped in his crib early this morning.",
        "Had a nice warm bath as part of bedtime routine.",
        "Family picnic lunch by the lake.",
        "Took a short nap in the car during the drive.",
        "She loves her evening bath before sleep."
    ]
    
    print("\n1. Single Text Classification")
    print("-" * 30)
    
    for text in test_texts[:3]:
        print(f"\nText: '{text}'")
        try:
            result = await classify_text(text)
            
            if result["pattern_id"]:
                print(f"✅ Matched: {result['pattern_id']}")
                print(f"   Confidence: {result['confidence']:.3f}")
                print(f"   Processing: {result['processing_time_ms']:.1f}ms")
                
                if result["alternatives"]:
                    print(f"   Alternatives:")
                    for alt in result["alternatives"][:2]:
                        print(f"     • {alt['pattern_id']} ({alt['confidence']:.3f})")
            else:
                print("❌ No match above threshold")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n\n2. Batch Classification")
    print("-" * 30)
    
    try:
        batch_result = await classify_batch(test_texts)
        print(f"Processed {batch_result['total']} texts:")
        
        for result in batch_result['results']:
            status = "✅" if result.get('pattern_id') else "❌"
            pattern_id = result.get('pattern_id', 'No match')
            confidence = result.get('confidence', 0)
            
            print(f"{status} {result['text'][:30]:<30} → {pattern_id} ({confidence:.3f})")
            
    except Exception as e:
        print(f"❌ Batch classification error: {e}")
    
    print("\n\n3. Service Statistics")
    print("-" * 30)
    
    try:
        stats = await get_service_stats()
        print(f"Total classifications: {stats['total_classifications']}")
        print(f"Average processing time: {stats['average_time_ms']:.1f}ms")
        print(f"Model: {stats['model_name']}")
        print(f"Collection: {stats['collection_name']}")
        
    except Exception as e:
        print(f"❌ Stats error: {e}")
    
    print("\n\n4. Domain Filtering Example")
    print("-" * 30)
    
    # Test domain filtering
    text = "He took a short nap this afternoon"
    
    for domain in [None, "child_development", "health"]:
        filter_text = f"(filter: {domain})" if domain else "(no filter)"
        print(f"\nText: '{text}' {filter_text}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SERVICE_URL}/classify",
                    json={
                        "text": text,
                        "confidence_threshold": 0.3,
                        "filter_by_domain": domain
                    }
                )
                result = response.json()
                
                if result["pattern_id"]:
                    print(f"✅ Matched: {result['pattern_id']} ({result['confidence']:.3f})")
                else:
                    print("❌ No match")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed! 🎉")


if __name__ == "__main__":
    asyncio.run(main()) 