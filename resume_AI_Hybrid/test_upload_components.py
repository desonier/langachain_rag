#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / 'common_tools'))

def test_file_processing():
    """Test file processing components to identify issues"""
    print("🧪 Testing file processing components...")
    
    # Test 1: Check if required libraries are available
    print("\n1️⃣ Testing library imports...")
    try:
        from langchain_community.document_loaders import Docx2txtLoader
        print("✅ Docx2txtLoader import successful")
    except ImportError as e:
        print(f"❌ Docx2txtLoader import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except Exception as e:
        print(f"❌ Environment loading failed: {e}")
    
    # Test 2: Check Azure OpenAI configuration
    print("\n2️⃣ Testing Azure OpenAI configuration...")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    if azure_endpoint:
        print(f"✅ Azure endpoint configured: {azure_endpoint[:50]}...")
    else:
        print("❌ Azure OpenAI endpoint not configured")
    
    if azure_key:
        print(f"✅ Azure key configured: {'*' * 20}")
    else:
        print("❌ Azure OpenAI key not configured")
    
    if azure_deployment:
        print(f"✅ Azure deployment configured: {azure_deployment}")
    else:
        print("❌ Azure deployment not configured")
    
    # Test 3: Check if we can initialize the ingest pipeline
    print("\n3️⃣ Testing ingest pipeline initialization...")
    try:
        from ingest_pipeline import ResumeIngestPipeline
        print("✅ ResumeIngestPipeline import successful")
        
        # Try to initialize without LLM to see basic functionality
        pipeline = ResumeIngestPipeline(collection_name="test_collection", enable_llm_parsing=False)
        print("✅ Pipeline initialization successful (without LLM)")
        
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        import traceback
        print(f"❌ Full error: {traceback.format_exc()}")
        return False
    
    # Test 4: Check ChromaDB connection
    print("\n4️⃣ Testing ChromaDB connection...")
    try:
        from shared_config import get_vector_db_path
        db_path = get_vector_db_path()
        print(f"✅ Database path: {db_path}")
        
        if os.path.exists(db_path):
            print("✅ Database directory exists")
        else:
            print("⚠️ Database directory does not exist")
        
    except Exception as e:
        print(f"❌ ChromaDB connection test failed: {e}")
    
    print("\n🎯 Component testing complete!")
    return True

if __name__ == "__main__":
    test_file_processing()