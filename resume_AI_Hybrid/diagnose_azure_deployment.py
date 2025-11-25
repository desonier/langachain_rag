#!/usr/bin/env python3
"""
Azure OpenAI Deployment Diagnostic Tool
Helps diagnose and fix deployment configuration issues
"""
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_azure_openai_deployments():
    """Check available deployments in Azure OpenAI resource"""
    print("🔍 Azure OpenAI Deployment Diagnostic")
    print("=" * 50)
    
    # Get configuration from environment
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    configured_deployment = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
    
    print(f"📍 Endpoint: {endpoint}")
    print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"📅 API Version: {api_version}")
    print(f"🚀 Configured Deployment: {configured_deployment}")
    print()
    
    if not endpoint or not api_key:
        print("❌ Missing required Azure OpenAI configuration")
        return
    
    # List deployments
    try:
        url = f"{endpoint}/openai/deployments"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        params = {
            "api-version": api_version
        }
        
        print(f"🌐 Requesting: {url}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            deployments = data.get("data", [])
            
            print(f"✅ Found {len(deployments)} deployments:")
            print()
            
            chat_deployments = []
            embedding_deployments = []
            
            for deployment in deployments:
                name = deployment.get("id", "Unknown")
                model = deployment.get("model", "Unknown")
                status = deployment.get("status", "Unknown")
                created = deployment.get("created_at", "Unknown")
                
                print(f"🚀 Deployment: {name}")
                print(f"   Model: {model}")
                print(f"   Status: {status}")
                print(f"   Created: {created}")
                print()
                
                # Categorize deployments
                if "gpt" in model.lower() or "chat" in model.lower():
                    chat_deployments.append(name)
                elif "embedding" in model.lower() or "ada" in model.lower():
                    embedding_deployments.append(name)
            
            # Check if configured deployment exists
            print("🎯 Deployment Analysis:")
            if configured_deployment in [d.get("id") for d in deployments]:
                print(f"✅ Configured deployment '{configured_deployment}' EXISTS")
            else:
                print(f"❌ Configured deployment '{configured_deployment}' NOT FOUND")
                print()
                print("💡 Available Chat/LLM deployments:")
                for deploy in chat_deployments:
                    print(f"   - {deploy}")
                print()
                print("💡 Available Embedding deployments:")
                for deploy in embedding_deployments:
                    print(f"   - {deploy}")
                print()
                print("🔧 Suggested fixes:")
                if chat_deployments:
                    print(f"   1. Update AZURE_OPENAI_CHATGPT_DEPLOYMENT to: {chat_deployments[0]}")
                print("   2. Create a deployment named 'resumemodel' in Azure OpenAI Studio")
                print("   3. Check deployment status - it may still be creating")
        
        elif response.status_code == 401:
            print("❌ Authentication failed - check your API key")
        elif response.status_code == 404:
            print("❌ Endpoint not found - check your Azure OpenAI endpoint URL")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - check your endpoint URL")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check your endpoint URL and internet connection")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_specific_deployment(deployment_name):
    """Test a specific deployment"""
    print(f"\n🧪 Testing deployment: {deployment_name}")
    print("-" * 30)
    
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    params = {
        "api-version": api_version
    }
    payload = {
        "messages": [{"role": "user", "content": "Hello, test connection"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Deployment '{deployment_name}' is working!")
        elif response.status_code == 404:
            print(f"❌ Deployment '{deployment_name}' not found")
        else:
            print(f"❌ Test failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

def suggest_fixes():
    """Provide suggested fixes"""
    print("\n🔧 Suggested Solutions:")
    print("=" * 30)
    print("1. 📋 Check Azure OpenAI Studio:")
    print("   - Go to https://oai.azure.com/")
    print("   - Navigate to your resource")
    print("   - Check 'Deployments' tab")
    print("   - Verify 'resumemodel' exists and is deployed")
    print()
    print("2. 🔄 Create Missing Deployment:")
    print("   - In Azure OpenAI Studio, click 'Create new deployment'")
    print("   - Use deployment name: 'resumemodel'")
    print("   - Select a GPT model (gpt-4, gpt-35-turbo, etc.)")
    print("   - Wait 5-10 minutes for deployment to complete")
    print()
    print("3. 🔧 Update Configuration:")
    print("   - If you have a different deployment name available")
    print("   - Update AZURE_OPENAI_CHATGPT_DEPLOYMENT in your .env file")
    print("   - Restart your application")
    print()
    print("4. ⚡ Quick Test Command:")
    print("   Run this script again in 5 minutes if you just created the deployment")

if __name__ == "__main__":
    check_azure_openai_deployments()
    
    # Test the currently configured deployment
    configured_deployment = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
    if configured_deployment:
        test_specific_deployment(configured_deployment)
    
    suggest_fixes()