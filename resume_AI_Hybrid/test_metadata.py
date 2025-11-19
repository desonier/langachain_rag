#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the admin module to path
admin_src_path = Path(__file__).parent / "common_tools" / "openwebui-resume-rag-admin" / "src"
sys.path.insert(0, str(admin_src_path))

try:
    from admin.chromadb_admin import ChromaDBAdmin
    import chromadb
    from shared_config import get_vector_db_path
    
    print("🔍 Testing metadata structure...")
    
    # Initialize ChromaDB client directly
    db_path = get_vector_db_path()
    client = chromadb.PersistentClient(path=db_path)
    
    # Get the collection
    collection = client.get_collection("coll1")
    
    # Query for some documents
    results = collection.query(
        query_texts=["cybersecurity"],
        n_results=5,
        include=["documents", "metadatas"]
    )
    
    print(f"📊 Found {len(results['documents'][0])} documents")
    
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\n📄 Document {i+1}:")
        print(f"  Content preview: {doc[:100]}...")
        print(f"  Metadata keys: {list(metadata.keys())}")
        
        # Check for filename fields
        for field in ['display_filename', 'original_file_source', 'document_name', 'source']:
            if field in metadata:
                print(f"  {field}: {metadata[field]}")
        
        # Show all metadata for first doc
        if i == 0:
            print(f"  Full metadata: {metadata}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()