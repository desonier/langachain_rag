#!/usr/bin/env python3
"""
Quick Ollama Cloud API key test
Simple validation script for testing API connectivity
"""

import requests
import json
import sys

def quick_test(api_key: str) -> bool:
    """Quick API key validation test"""
    
    print(f"🧪 Testing API key: {'*' * (len(api_key) - 4) + api_key[-4:]}")
    
    # Test endpoint
    url = "https://ollama.com/api/tags"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        print("📡 Connecting to Ollama Cloud...")
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: API key is valid!")
            try:
                data = response.json()
                models = data.get("models", [])
                print(f"🤖 Available models: {len(models)}")
                return True
            except:
                print("⚠️  Valid key but unexpected response format")
                return True
                
        elif response.status_code == 401:
            print("❌ FAILED: Invalid API key (401 Unauthorized)")
            print("💡 Get a new key from: https://ollama.com/settings/keys")
            return False
            
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Cannot connect to Ollama Cloud")
        print("💡 Check your internet connection")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ FAILED: Request timeout")
        print("💡 Ollama Cloud may be slow or unavailable")
        return False
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    print("🦙 Ollama Cloud API Key Quick Test")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = input("Enter your Ollama Cloud API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        sys.exit(1)
    
    success = quick_test(api_key)
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 API key test PASSED!")
        print("You can now use this key in your application.")
    else:
        print("💥 API key test FAILED!")
        print("Please check your API key and try again.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()