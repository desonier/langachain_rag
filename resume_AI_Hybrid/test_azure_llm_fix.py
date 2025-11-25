#!/usr/bin/env python3
"""
Test Azure OpenAI LLM connection after fixing deployment_name parameter
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path to import shared_config
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_azure_llm_connection():
    """Test Azure LLM connection with correct parameters"""
    print("🧪 Testing Azure OpenAI LLM Connection")
    print("=" * 40)
    
    try:
        from shared_config import get_dynamic_llm_config
        from langchain_openai import AzureChatOpenAI
        
        # Get LLM configuration
        llm_config = get_dynamic_llm_config("azure-openai", "resumemodel")
        
        print("🔧 LLM Configuration:")
        for key, value in llm_config.items():
            if key == "api_key":
                print(f"   {key}: {'***' + value[-4:] if value else 'None'}")
            else:
                print(f"   {key}: {value}")
        print()
        
        # Create LLM instance
        print("🚀 Creating Azure OpenAI LLM instance...")
        llm = AzureChatOpenAI(**llm_config)
        print("✅ LLM instance created successfully")
        
        # Test connection
        print("\n📡 Testing connection...")
        response = llm.invoke("Test connection. Reply with: OK")
        
        print("✅ Connection test successful!")
        print(f"📝 Response: {response.content[:100]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_fallback_connection():
    """Test with fallback configuration"""
    print("\n🔄 Testing with fallback configuration...")
    try:
        from langchain_openai import AzureChatOpenAI
        
        # Direct configuration without shared_config
        llm = AzureChatOpenAI(
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_KEY'),
            azure_deployment=os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
            temperature=0.1
        )
        
        response = llm.invoke("Test connection. Reply with: OK")
        print("✅ Fallback connection successful!")
        print(f"📝 Response: {response.content[:100]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Azure OpenAI Connection Test")
    print("=" * 50)
    
    # Show current environment
    print("📋 Environment Configuration:")
    print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    print(f"   Deployment: {os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT')}")
    print(f"   API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
    print(f"   API Key: {'Set' if os.getenv('AZURE_OPENAI_KEY') else 'Missing'}")
    print()
    
    success1 = test_azure_llm_connection()
    
    if not success1:
        success2 = test_fallback_connection()
        if success2:
            print("\n💡 Fallback works - there may be an issue with shared_config import")
    
    print("\n" + "=" * 50)
    if success1:
        print("🎉 Configuration fixed! Your Azure OpenAI connection is working.")
    else:
        print("❌ Still having issues. Check your Azure OpenAI deployment.")