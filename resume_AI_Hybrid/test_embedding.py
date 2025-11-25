#!/usr/bin/env python3
"""
Simple script to test embedding function creation for different providers
"""
import os
import sys
sys.path.append(r'C:\Users\DamonDesonier\repos\langachain_rag\resume_AI_Hybrid\common_tools\openwebui-resume-rag-admin\src')

def test_embedding_function(provider, model):
    """Test embedding function creation for a specific provider and model"""
    print(f"\n🧪 Testing {provider} with model: {model}")
    
    try:
        import chromadb.utils.embedding_functions as embedding_functions
        
        if provider == "huggingface":
            try:
                embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=model,
                    device="cpu",
                    normalize_embeddings=True
                )
                
                # Test with sample text
                result = embedding_func(["test text"])
                dim = len(result[0]) if result else "Unknown"
                print(f"✅ Success! Dimensions: {dim}")
                return True
                
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
                
        elif provider == "azure-openai":
            azure_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            
            if not azure_key:
                print("❌ Missing Azure OpenAI API key (AZURE_OPENAI_API_KEY)")
                return False
            if not azure_endpoint:
                print("❌ Missing Azure OpenAI endpoint (AZURE_OPENAI_ENDPOINT)")
                return False
                
            try:
                embedding_func = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=azure_key,
                    api_base=azure_endpoint,
                    api_type="azure",
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                    model_name=model
                )
                
                # Test with sample text
                result = embedding_func(["test text"])
                dim = len(result[0]) if result else "Unknown"
                print(f"✅ Success! Dimensions: {dim}")
                return True
                
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
                
        elif provider == "openai":
            openai_key = os.getenv("OPENAI_API_KEY")
            
            if not openai_key:
                print("❌ Missing OpenAI API key (OPENAI_API_KEY)")
                return False
                
            try:
                embedding_func = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=openai_key,
                    model_name=model
                )
                
                # Test with sample text
                result = embedding_func(["test text"])
                dim = len(result[0]) if result else "Unknown"
                print(f"✅ Success! Dimensions: {dim}")
                return True
                
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    print("🚀 Testing Embedding Functions")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        ("huggingface", "sentence-transformers/all-MiniLM-L6-v2"),
        ("azure-openai", "text-embedding-ada-002"),
        ("openai", "text-embedding-ada-002"),
    ]
    
    results = {}
    for provider, model in test_cases:
        results[provider] = test_embedding_function(provider, model)
    
    print("\n📊 Results Summary")
    print("=" * 50)
    for provider, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"{provider:15} : {status}")
    
    print("\n💡 Environment Variables:")
    env_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT", 
        "AZURE_OPENAI_API_VERSION",
        "OPENAI_API_KEY"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"{var:25} : {masked}")
        else:
            print(f"{var:25} : Not set")

if __name__ == "__main__":
    main()