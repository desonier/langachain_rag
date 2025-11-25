#!/usr/bin/env python3
"""
Test script for Ollama Cloud API key validation
Tests direct API connection to Ollama Cloud service
"""

import os
import json
import requests
from typing import Dict, Any

def test_ollama_cloud_api(api_key: str = None, model: str = "gpt-oss:120b-cloud") -> Dict[str, Any]:
    """
    Test Ollama Cloud API connection with the provided API key
    
    Args:
        api_key: Ollama Cloud API key (if None, tries to get from environment)
        model: Model to test with (default: gpt-oss:120b-cloud)
        
    Returns:
        Dictionary with test results
    """
    # Get API key from parameter or environment
    if not api_key:
        api_key = os.getenv('OLLAMA_API_KEY')
    
    if not api_key:
        return {
            "success": False,
            "error": "No API key provided. Set OLLAMA_API_KEY environment variable or pass as parameter."
        }
    
    # Test configuration
    base_url = "https://ollama.com"
    api_endpoint = f"{base_url}/api/chat"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test payload
    test_payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Hello! Please respond with 'API test successful' if you can see this message."
            }
        ],
        "stream": False
    }
    
    print(f"🧪 Testing Ollama Cloud API...")
    print(f"📡 Endpoint: {api_endpoint}")
    print(f"🤖 Model: {model}")
    print(f"🔑 API Key: {'*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****'}")
    print("-" * 60)
    
    try:
        # Make the API request
        response = requests.post(
            api_endpoint,
            headers=headers,
            json=test_payload,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                message_content = response_data.get("message", {}).get("content", "")
                
                print(f"✅ Success! Response: {message_content[:200]}...")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": message_content,
                    "model": model
                }
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"🔍 Raw response: {response.text[:500]}...")
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {e}",
                    "status_code": response.status_code,
                    "raw_response": response.text[:500]
                }
        
        elif response.status_code == 401:
            print(f"❌ Authentication failed (401)")
            print(f"🔍 Response: {response.text[:200]}...")
            return {
                "success": False,
                "error": "Authentication failed. Please check your API key.",
                "status_code": response.status_code,
                "suggestion": "Get a new API key from https://ollama.com/settings/keys"
            }
            
        elif response.status_code == 404:
            print(f"❌ Model or endpoint not found (404)")
            print(f"🔍 Response: {response.text[:200]}...")
            return {
                "success": False,
                "error": f"Model '{model}' not found or endpoint incorrect.",
                "status_code": response.status_code,
                "suggestion": "Check if the model name is correct and available in Ollama Cloud"
            }
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"🔍 Response: {response.text[:300]}...")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:100]}",
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        error_msg = "Request timeout (30s). Ollama Cloud may be slow or unavailable."
        print(f"⏱️ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {e}"
        print(f"🔌 {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"💥 {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }


def test_available_models(api_key: str = None) -> Dict[str, Any]:
    """
    Test listing available models from Ollama Cloud
    
    Args:
        api_key: Ollama Cloud API key
        
    Returns:
        Dictionary with available models or error
    """
    if not api_key:
        api_key = os.getenv('OLLAMA_API_KEY')
    
    if not api_key:
        return {
            "success": False,
            "error": "No API key provided"
        }
    
    base_url = "https://ollama.com"
    api_endpoint = f"{base_url}/api/tags"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔍 Testing available models...")
    print(f"📡 Endpoint: {api_endpoint}")
    
    try:
        response = requests.get(api_endpoint, headers=headers, timeout=15)
        
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get("models", [])
            
            print(f"✅ Found {len(models)} available models:")
            for model in models[:5]:  # Show first 5 models
                print(f"   🤖 {model.get('name', 'Unknown')}")
            
            return {
                "success": True,
                "models": models,
                "count": len(models)
            }
        else:
            print(f"❌ Failed to get models: HTTP {response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:100]}"
            }
            
    except Exception as e:
        print(f"❌ Error getting models: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main test function"""
    print("=" * 60)
    print("🦙 OLLAMA CLOUD API KEY TEST")
    print("=" * 60)
    
    # Get API key from user input if not in environment
    api_key = os.getenv('OLLAMA_API_KEY')
    
    if not api_key:
        print("⚠️  No OLLAMA_API_KEY environment variable found.")
        api_key = input("🔑 Please enter your Ollama Cloud API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return
    
    # Test 1: List available models
    print("\n" + "="*60)
    print("TEST 1: AVAILABLE MODELS")
    print("="*60)
    models_result = test_available_models(api_key)
    
    # Test 2: Chat API with default model
    print("\n" + "="*60)
    print("TEST 2: CHAT API TEST")
    print("="*60)
    chat_result = test_ollama_cloud_api(api_key)
    
    # Test 3: Try alternative models if available
    if models_result.get("success") and models_result.get("models"):
        available_models = models_result["models"]
        cloud_models = [m for m in available_models if "cloud" in m.get("name", "").lower()]
        
        if cloud_models:
            test_model = cloud_models[0]["name"]
            print(f"\n" + "="*60)
            print(f"TEST 3: ALTERNATIVE MODEL ({test_model})")
            print("="*60)
            alt_result = test_ollama_cloud_api(api_key, test_model)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    if models_result.get("success"):
        print("✅ Model listing: SUCCESS")
    else:
        print(f"❌ Model listing: FAILED - {models_result.get('error', 'Unknown error')}")
    
    if chat_result.get("success"):
        print("✅ Chat API: SUCCESS")
    else:
        print(f"❌ Chat API: FAILED - {chat_result.get('error', 'Unknown error')}")
    
    # Provide next steps
    print("\n" + "="*60)
    print("🚀 NEXT STEPS")
    print("="*60)
    
    if chat_result.get("success"):
        print("✅ Your Ollama Cloud API key is working!")
        print("💡 You can now use this API key in your Flask application.")
        print("🔧 Set the OLLAMA_API_KEY environment variable or enter it in the UI.")
    else:
        print("❌ API key test failed. Please:")
        print("   1. Check your API key at https://ollama.com/settings/keys")
        print("   2. Make sure your account has access to Ollama Cloud")
        print("   3. Try generating a new API key")
        print("   4. Check your internet connection")


if __name__ == "__main__":
    main()