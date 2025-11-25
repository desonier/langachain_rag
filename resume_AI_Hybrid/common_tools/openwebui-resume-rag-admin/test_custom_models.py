#!/usr/bin/env python3
"""
Test script for custom model management functionality
"""
import sys
import os
import json
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

# Import the custom model functions
from main import save_custom_model, load_custom_models

def test_custom_model_management():
    """Test the custom model save and load functionality"""
    print("🧪 Testing Custom Model Management System")
    print("=" * 50)
    
    # Test 1: Save custom LLM model
    print("📝 Test 1: Saving custom LLM model...")
    try:
        save_custom_model('llm', 'azure-openai', 'my-custom-gpt-model')
        print("✅ Custom LLM model saved successfully")
    except Exception as e:
        print(f"❌ Error saving LLM model: {e}")
    
    # Test 2: Save custom embedding model
    print("\n📝 Test 2: Saving custom embedding model...")
    try:
        save_custom_model('embedding', 'huggingface', 'my-custom-embedding-model')
        print("✅ Custom embedding model saved successfully")
    except Exception as e:
        print(f"❌ Error saving embedding model: {e}")
    
    # Test 3: Load custom models
    print("\n📝 Test 3: Loading custom models...")
    try:
        custom_models = load_custom_models()
        print("✅ Custom models loaded successfully")
        print(f"📊 Custom models structure:")
        print(json.dumps(custom_models, indent=2))
    except Exception as e:
        print(f"❌ Error loading custom models: {e}")
    
    # Test 4: Verify file creation
    custom_models_file = src_dir / 'custom_models.json'
    if custom_models_file.exists():
        print(f"\n✅ Custom models file created at: {custom_models_file}")
        with open(custom_models_file, 'r') as f:
            content = json.load(f)
        print(f"📄 File contents:")
        print(json.dumps(content, indent=2))
    else:
        print(f"\n❌ Custom models file not found at: {custom_models_file}")
    
    print("\n" + "=" * 50)
    print("🎉 Custom Model Management Test Complete!")

if __name__ == "__main__":
    test_custom_model_management()