#!/usr/bin/env python3
"""
Clean Azure OpenAI test endpoint to demonstrate working connection
This can be run independently or integrated into the main app
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_openai_connection(model_name="resumemodel"):
    """Test Azure OpenAI connection with clean imports"""
    try:
        # Import at function level to avoid module conflicts
        from langchain_openai import AzureChatOpenAI
        
        # Configuration
        config = {
            'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'api_key': os.getenv('AZURE_OPENAI_KEY'), 
            'azure_deployment': model_name,
            'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
            'temperature': 0.1
        }
        
        print(f"🧪 Testing Azure OpenAI connection...")
        print(f"📍 Endpoint: {config['azure_endpoint']}")
        print(f"🚀 Deployment: {model_name}")
        
        # Create LLM instance
        llm = AzureChatOpenAI(**config)
        
        # Test connection
        response = llm.invoke("Test connection. Reply with: OK")
        
        result = {
            "success": True,
            "message": "✅ Azure OpenAI connection successful",
            "response": response.content[:100] if hasattr(response, 'content') else str(response)[:100],
            "config": {k: v for k, v in config.items() if k != 'api_key'}  # Don't return API key
        }
        
        print(f"✅ SUCCESS: {result['response']}")
        return result
        
    except Exception as e:
        import traceback
        error_result = {
            "success": False,
            "error": f"Azure OpenAI test failed: {str(e)}",
            "traceback": traceback.format_exc()
        }
        print(f"❌ ERROR: {str(e)}")
        return error_result

if __name__ == "__main__":
    # Run test
    result = test_azure_openai_connection()
    
    if result["success"]:
        print(f"\n🎉 Connection test PASSED!")
        print(f"Response: {result['response']}")
    else:
        print(f"\n💥 Connection test FAILED!")
        print(f"Error: {result['error']}")