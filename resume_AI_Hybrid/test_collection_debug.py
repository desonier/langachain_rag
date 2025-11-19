#!/usr/bin/env python3
"""
Debug script for testing new collection queries
This will help identify why new collections aren't returning results
"""

import requests
import json

def test_collections_and_query():
    """Test collection creation and querying"""
    
    base_url = "http://localhost:5001"
    
    print("🔍 Testing Collections and Queries")
    print("=" * 50)
    
    # 1. List all collections
    try:
        print("📋 Step 1: Listing all collections...")
        response = requests.get(f"{base_url}/api/collections")
        if response.status_code == 200:
            collections = response.json()
            print(f"✅ Found {len(collections)} collections:")
            for i, col in enumerate(collections, 1):
                print(f"   {i}. {col['name']} ({col.get('count', 'unknown')} documents)")
        else:
            print(f"❌ Failed to list collections: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error listing collections: {e}")
        return
    
    # 2. Test queries on each collection
    test_queries = [
        "experience",
        "skills", 
        "education",
        "test"
    ]
    
    for query_text in test_queries:
        print(f"\n🔍 Testing query: '{query_text}'")
        print("-" * 30)
        
        for collection in collections:
            coll_name = collection['name']
            print(f"📊 Collection: {coll_name}")
            
            # Test ranking query
            payload = {
                "query": query_text,
                "collection": coll_name,
                "query_type": "ranking",
                "max_results": 3
            }
            
            try:
                response = requests.post(f"{base_url}/api/query", json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        results_count = len(result.get('results', []))
                        print(f"   ✅ Ranking: {results_count} results")
                        if results_count == 0:
                            print("   ⚠️  No results returned")
                        else:
                            # Show first result sample
                            first_result = result['results'][0]
                            print(f"   📄 Sample: {first_result.get('content', '')[:100]}...")
                    else:
                        print(f"   ❌ Query failed: {result.get('error', 'Unknown error')}")
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    print(f"   📝 Response: {response.text}")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
    
    # 3. Test creating a new collection
    print(f"\n🆕 Testing new collection creation...")
    new_collection_name = "test_collection_debug"
    
    try:
        create_payload = {"collection_name": new_collection_name}
        response = requests.post(f"{base_url}/api/collections", json=create_payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Created collection: {new_collection_name}")
                
                # Try to query the empty collection
                query_payload = {
                    "query": "test",
                    "collection": new_collection_name,
                    "query_type": "ranking",
                    "max_results": 3
                }
                
                query_response = requests.post(f"{base_url}/api/query", json=query_payload, timeout=30)
                if query_response.status_code == 200:
                    query_result = query_response.json()
                    print(f"✅ Query on new collection successful")
                    print(f"📊 Results: {len(query_result.get('results', []))}")
                else:
                    print(f"❌ Query on new collection failed: {query_response.status_code}")
                    print(f"📝 Response: {query_response.text}")
            else:
                print(f"❌ Failed to create collection: {result.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error creating collection: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception creating collection: {e}")
    
    print(f"\n🏁 Debug test completed!")

if __name__ == "__main__":
    test_collections_and_query()