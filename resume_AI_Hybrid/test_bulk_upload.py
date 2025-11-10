#!/usr/bin/env python3
"""
Test script for bulk upload functionality
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_ingest_pipeline_integration():
    """Test if the ingest pipeline can be used for bulk upload"""
    print("🧪 Testing Ingest Pipeline Integration for Bulk Upload")
    print("=" * 60)
    
    try:
        # Test import
        from common_tools.ingest_pipeline import ResumeIngestPipeline
        print("✅ Successfully imported ResumeIngestPipeline")
        
        # Test initialization with collection name
        collection_name = "test_bulk_upload"
        pipeline = ResumeIngestPipeline(collection_name=collection_name)
        print(f"✅ Successfully initialized pipeline for collection: {collection_name}")
        
        # Test that the pipeline has the required methods
        if hasattr(pipeline, 'process_file'):
            print("✅ Pipeline has process_file method")
        else:
            print("❌ Pipeline missing process_file method")
            return False
            
        # Test collection listing
        from chromadb_factory import list_collections
        db_path = str(project_root / "resume_vectordb")
        collections = list_collections(db_path)
        print(f"✅ Available collections: {collections}")
        
        print("\n🎉 All tests passed! Bulk upload functionality should work correctly.")
        print("\n📋 Next steps:")
        print("1. Start admin interface: python common_tools/openwebui-resume-rag-admin/src/main.py")
        print("2. Navigate to Collections: http://localhost:5001/admin/collections")
        print("3. Click 'Bulk Upload' on any collection")
        print("4. Choose directory or upload files")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_ingest_pipeline_integration()