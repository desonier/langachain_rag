#!/usr/bin/env python3
"""Test script to debug the PromptTemplate error"""

import requests
import json

def test_query():
    """Test the query API to reproduce the PromptTemplate error"""
    
    url = "http://localhost:5001/api/query"
    
    payload = {
        "query": "test query",
        "collection": "coll1",
        "query_type": "rag",
        "max_results": 3
    }
    
    try:
        print("🧪 Testing query API...")
        print(f"📡 URL: {url}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"🔍 Status Code: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Query successful!")
            print(f"📊 Results: {json.dumps(result, indent=2)}")
        else:
            print("❌ Query failed!")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ General error: {e}")

if __name__ == "__main__":
    test_query()