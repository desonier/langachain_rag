#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'common_tools', 'openwebui-resume-rag-admin', 'src'))

from admin.chromadb_admin import ChromaDBAdmin
from shared_config import get_vector_db_path

def debug_collections():
    """Debug what data is in the collections"""
    print("🔍 Debugging collection data...")
    
    # Initialize ChromaDBAdmin
    db_path = get_vector_db_path()
    admin = ChromaDBAdmin(db_path)
    
    # Get collections
    collections = admin.list_collections()
    print(f"📊 Found {len(collections)} collections")
    
    for collection in collections:
        print(f"\n🗂️ Collection: {collection}")
        
        # Check raw data in the collection
        try:
            client = admin.get_client()
            chroma_collection = client.get_collection(collection['name'])
            
            # Get some data to see what's actually stored
            data = chroma_collection.get(limit=3, include=["metadatas", "documents"])
            print(f"📄 Raw data sample:")
            print(f"  - Documents: {len(data.get('documents', []))}")
            print(f"  - Metadatas: {data.get('metadatas', [])}")
            print(f"  - First document preview: {str(data.get('documents', [''])[0])[:100]}...")
            
        except Exception as e:
            print(f"❌ Error getting collection data: {e}")

if __name__ == "__main__":
    debug_collections()