#!/usr/bin/env python3
"""
Minimal Flask app to test model selection functionality
"""
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/api/models/test', methods=['POST'])
def test_model_connection():
    """Test connection to specified model"""
    data = request.get_json()
    provider = data.get('provider')
    model = data.get('model')
    test_type = data.get('test_type')
    
    print(f"Testing {test_type} - Provider: {provider}, Model: {model}")
    
    try:
        if test_type == 'embedding':
            import chromadb.utils.embedding_functions as embedding_functions
            
            if provider == "huggingface":
                try:
                    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=model,
                        device="cpu",
                        normalize_embeddings=True
                    )
                    
                    # Test with sample text
                    test_result = embedding_function(["test text"])
                    return jsonify({
                        "success": True,
                        "message": f"✅ Embedding model connection successful",
                        "dimensions": len(test_result[0]) if test_result and len(test_result) > 0 else "Unknown"
                    })
                except Exception as e:
                    return jsonify({
                        "success": False,
                        "error": f"HuggingFace embedding test failed: {str(e)}"
                    })
                    
            elif provider == "azure-openai":
                azure_key = os.getenv("AZURE_OPENAI_API_KEY")
                azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                
                if not azure_key or not azure_endpoint:
                    return jsonify({
                        "success": False,
                        "error": f"Missing Azure configuration. Key: {bool(azure_key)}, Endpoint: {bool(azure_endpoint)}"
                    })
                    
                try:
                    embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                        api_key=azure_key,
                        api_base=azure_endpoint,
                        api_type="azure",
                        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                        model_name=model,
                        deployment_id=model  # Use model as deployment ID
                    )
                    
                    # Test with sample text
                    test_result = embedding_function(["test text"])
                    return jsonify({
                        "success": True,
                        "message": f"✅ Azure embedding model connection successful",
                        "dimensions": len(test_result[0]) if test_result and len(test_result) > 0 else "Unknown"
                    })
                except Exception as e:
                    return jsonify({
                        "success": False,
                        "error": f"Azure embedding test failed: {str(e)}"
                    })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Provider {provider} not implemented in minimal test"
                })
                
        return jsonify({
            "success": False,
            "error": "Invalid test type or not implemented"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Test error: {str(e)}"
        })

@app.route('/test')
def test_page():
    """Simple test page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Model Test</title>
        <script>
        function testEmbedding(provider, model) {
            fetch('/api/models/test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    provider: provider,
                    model: model,
                    test_type: 'embedding'
                })
            })
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('result-' + provider);
                if (data.success) {
                    resultDiv.innerHTML = '<span style="color: green">' + data.message + '</span>';
                    if (data.dimensions) {
                        resultDiv.innerHTML += '<br><small>Dimensions: ' + data.dimensions + '</small>';
                    }
                } else {
                    resultDiv.innerHTML = '<span style="color: red">❌ ' + data.error + '</span>';
                }
            })
            .catch(error => {
                const resultDiv = document.getElementById('result-' + provider);
                resultDiv.innerHTML = '<span style="color: red">❌ Network error: ' + error.message + '</span>';
            });
        }
        </script>
    </head>
    <body>
        <h1>Model Connection Test</h1>
        
        <h2>HuggingFace Embedding</h2>
        <button onclick="testEmbedding('huggingface', 'sentence-transformers/all-MiniLM-L6-v2')">
            Test HuggingFace
        </button>
        <div id="result-huggingface"></div>
        
        <h2>Azure OpenAI Embedding</h2>
        <button onclick="testEmbedding('azure-openai', 'text-embedding-ada-002')">
            Test Azure OpenAI
        </button>
        <div id="result-azure-openai"></div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🚀 Starting minimal model test server...")
    print("📱 Open http://localhost:5002/test to test embedding functions")
    app.run(debug=True, host='0.0.0.0', port=5002)