#!/usr/bin/env python3

import requests
import json

def test_query():
    """Test the query API directly to trigger debug output"""
    url = "http://localhost:5001/api/query"
    
    payload = {
        "query": "cybersecurity experience",
        "collection": "coll1",
        "query_type": "standard",
        "max_results": 5
    }
    
    try:
        print("🧪 Sending test query...")
        response = requests.post(url, json=payload)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query successful")
            print(f"📈 Number of results: {len(data.get('results', []))}")
            
            # Check source documents
            for result in data.get('results', []):
                sources = result.get('sources', [])
                print(f"🗂️ Collection '{result.get('collection')}' has {len(sources)} source documents")
                for i, source in enumerate(sources):
                    original_name = source.get('original_filename', source.get('metadata', {}).get('display_filename', 'Unknown'))
                    chunk_count = source.get('chunk_count', 1)
                    print(f"   Document {i+1}: {original_name} ({chunk_count} chunks)")
        else:
            print(f"❌ Query failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_query()