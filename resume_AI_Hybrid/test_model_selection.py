#!/usr/bin/env python3
"""
Test script to verify that model selection in the Query Tab actually changes the LLM being used
"""
import requests
import json
import time

# Base URL for the admin interface
BASE_URL = "http://localhost:5001"

def test_model_selection():
    """Test different model selections to see if they produce different responses"""
    
    # Test query
    test_query = "What is the name mentioned in the resume?"
    
    # Different model configurations to test
    test_models = [
        {"model": "azure-openai:resumemodel", "temperature": 0.1},
        {"model": "azure-openai:resumemodel", "temperature": 0.9},
        # Add more models when available
    ]
    
    print(f"🧪 Testing Model Selection with Query: '{test_query}'")
    print("=" * 60)
    
    results = []
    
    for i, model_config in enumerate(test_models, 1):
        print(f"\n🔄 Test {i}: {model_config['model']} (temp: {model_config['temperature']})")
        
        # Prepare API request
        payload = {
            "query": test_query,
            "collection": "all",  # Query all collections
            "query_type": "standard",
            "max_results": 3,
            "model": model_config["model"],
            "temperature": model_config["temperature"]
        }
        
        try:
            # Make request
            response = requests.post(
                f"{BASE_URL}/api/query",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # Extract the answer from the result
                    answer = result.get("result", {}).get("answer", "No answer provided")
                    print(f"✅ Response received: {answer[:200]}...")
                    results.append({
                        "model": model_config["model"],
                        "temperature": model_config["temperature"],
                        "answer": answer,
                        "status": "success"
                    })
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(f"❌ Query failed: {error_msg}")
                    results.append({
                        "model": model_config["model"],
                        "temperature": model_config["temperature"],
                        "error": error_msg,
                        "status": "error"
                    })
            else:
                print(f"❌ HTTP Error: {response.status_code} - {response.text}")
                results.append({
                    "model": model_config["model"],
                    "temperature": model_config["temperature"],
                    "error": f"HTTP {response.status_code}",
                    "status": "http_error"
                })
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
            results.append({
                "model": model_config["model"],
                "temperature": model_config["temperature"],
                "error": str(e),
                "status": "request_error"
            })
        
        # Wait between requests
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY:")
    print("=" * 60)
    
    for i, result in enumerate(results, 1):
        print(f"\nTest {i}: {result['model']} (temp: {result.get('temperature', 'N/A')})")
        if result['status'] == 'success':
            print(f"  ✅ Success: {result['answer'][:100]}...")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Compare answers for temperature differences
    if len([r for r in results if r['status'] == 'success']) >= 2:
        print(f"\n🔍 ANALYSIS:")
        print("-" * 40)
        successful_results = [r for r in results if r['status'] == 'success']
        
        # Compare answers
        answers = [r['answer'] for r in successful_results]
        if len(set(answers)) > 1:
            print("✅ Different models/temperatures produced DIFFERENT answers!")
            print("   This suggests model selection is working correctly.")
        else:
            print("⚠️ All models/temperatures produced IDENTICAL answers.")
            print("   This might indicate model selection is not working,")
            print("   or the query is simple enough that all models give the same response.")
    
    return results

if __name__ == "__main__":
    print("🧪 Model Selection Test Script")
    print("Testing if different model selections actually change LLM behavior...")
    
    # Check if admin interface is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Admin interface is running")
            test_model_selection()
        else:
            print(f"❌ Admin interface responded with status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to admin interface: {e}")
        print("   Make sure the Flask app is running on localhost:5001")