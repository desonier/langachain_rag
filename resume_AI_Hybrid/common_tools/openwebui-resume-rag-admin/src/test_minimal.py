#!/usr/bin/env python3
"""
Minimal Flask app to test Azure OpenAI connection without complex imports
"""
from flask import Flask, jsonify, request
import os
import sys

app = Flask(__name__)

@app.route('/api/test-basic', methods=['POST'])
def test_basic():
    """Basic test without langchain"""
    try:
        data = request.get_json()
        provider = data.get('provider')
        model = data.get('model')
        
        # Get environment variables
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_KEY')
        api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        
        return jsonify({
            "success": True,
            "message": "Basic test successful",
            "provider": provider,
            "model": model,
            "endpoint": endpoint[:30] + "..." if endpoint else None,
            "api_key": "***" if api_key else None,
            "api_version": api_version
        })
    except Exception as e:
        import traceback
        print(f"Basic test error: {e}")
        print(f"Basic test traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/test-langchain', methods=['POST'])
def test_langchain():
    """Test with langchain import"""
    try:
        # Import langchain at function level to isolate any issues
        from langchain_openai import AzureChatOpenAI
        
        data = request.get_json()
        model = data.get('model', 'resumemodel')
        
        # Get configuration with validation
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_KEY') or os.getenv('AZURE_OPENAI_API_KEY')  
        api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        
        if not endpoint:
            return jsonify({"success": False, "error": "Azure OpenAI endpoint not configured"})
        if not api_key:
            return jsonify({"success": False, "error": "Azure OpenAI API key not configured"})
        if not api_version:
            return jsonify({"success": False, "error": "Azure OpenAI API version not configured"})
        
        llm_config = {
            'azure_endpoint': endpoint,
            'api_key': api_key,
            'azure_deployment': model,
            'api_version': api_version,
            'temperature': 0.1
        }
        
        print(f"DEBUG: Testing Azure OpenAI with deployment: {model}")
        print(f"DEBUG: API Version: {api_version}")
        print(f"DEBUG: Endpoint: {endpoint[:50]}...")
        
        # Create and test LLM
        llm = AzureChatOpenAI(**llm_config)
        response = llm.invoke("Test connection. Reply with: OK")
        
        return jsonify({
            "success": True,
            "message": "LangChain test successful",
            "response": response.content[:100] if hasattr(response, 'content') else str(response)[:100]
        })
    except Exception as e:
        import traceback
        print(f"LangChain test error: {e}")
        print(f"LangChain test traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    print("Starting minimal test Flask app...")
    app.run(host='0.0.0.0', port=5002, debug=True)