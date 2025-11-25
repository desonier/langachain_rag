#!/usr/bin/env python3
"""
Direct Azure OpenAI test to verify the 404 issue is resolved
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_direct_azure_openai():
    """Test Azure OpenAI directly with the parameters from your environment"""
    print("🧪 Direct Azure OpenAI Test")
    print("=" * 40)
    
    # Show environment configuration
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    deployment = os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT')
    api_key = os.getenv('AZURE_OPENAI_KEY')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
    
    print(f"📍 Endpoint: {endpoint}")
    print(f"🚀 Deployment: {deployment}")
    print(f"📅 API Version: {api_version}")
    print(f"🔑 API Key: {'Set' if api_key else 'Missing'}")
    print()
    
    try:
        from langchain_openai import AzureChatOpenAI
        
        # Test 1: With the configured deployment name
        print("🧪 Test 1: Using configured deployment 'resumemodel'")
        llm_config = {
            'azure_endpoint': endpoint,
            'api_key': api_key,
            'azure_deployment': deployment,  # This should be 'resumemodel'
            'api_version': api_version,
            'temperature': 0.1
        }
        
        print(f"🔧 Config: {llm_config}")
        llm = AzureChatOpenAI(**llm_config)
        
        response = llm.invoke("Test connection. Reply with: OK")
        print(f"✅ SUCCESS: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        
        # Test 2: Try with different common deployment names
        print("\\n🔄 Trying common deployment names...")
        common_names = ['gpt-4', 'gpt-35-turbo', 'chatgpt', 'gpt-4-turbo']
        
        for test_deployment in common_names:
            try:
                print(f"   Testing: {test_deployment}")
                test_config = {
                    'azure_endpoint': endpoint,
                    'api_key': api_key,
                    'azure_deployment': test_deployment,
                    'api_version': api_version,
                    'temperature': 0.1
                }
                
                test_llm = AzureChatOpenAI(**test_config)
                test_response = test_llm.invoke("Test")
                print(f"   ✅ {test_deployment} WORKS!")
                print(f"   💡 Suggestion: Update AZURE_OPENAI_CHATGPT_DEPLOYMENT to '{test_deployment}'")
                return True
                
            except Exception as test_e:
                print(f"   ❌ {test_deployment} failed: {test_e}")
        
        return False

if __name__ == "__main__":
    test_direct_azure_openai()