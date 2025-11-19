#!/usr/bin/env python3
"""
Test script for collection creation
"""

import requests
import json
import time

def test_collection_creation():
    """Test creating a new collection"""
    
    base_url = "http://localhost:5001"
    test_collection_name = f"test_collection_{int(time.time())}"
    
    print(f"🧪 Testing collection creation: {test_collection_name}")
    
    try:
        # Test collection creation
        create_payload = {"name": test_collection_name}  # Fixed payload key
        
        print("📡 Sending collection creation request...")
        start_time = time.time()
        
        response = requests.post(f"{base_url}/api/collections", json=create_payload, timeout=60)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Request took: {duration:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Collection created successfully!")
                print(f"📝 Message: {result.get('message', 'No message')}")
                
                # Test listing collections
                print("\n📋 Testing collection listing...")
                list_response = requests.get(f"{base_url}/api/collections")
                if list_response.status_code == 200:
                    collections = list_response.json()
                    print(f"✅ Found {len(collections)} collections:")
                    for col in collections:
                        if isinstance(col, dict):  # Check if it's a dict
                            print(f"   - {col.get('name', 'Unknown')} ({col.get('count', 0)} documents)")
                            if col.get('name') == test_collection_name:
                                print("   ✅ New collection found in list!")
                        else:
                            print(f"   - {col}")  # Handle string or other types
                else:
                    print(f"❌ Failed to list collections: {list_response.status_code}")
                
            else:
                print(f"❌ Collection creation failed: {result.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (collection creation hung)")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_collection_creation()