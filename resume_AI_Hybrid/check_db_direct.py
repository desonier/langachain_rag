#!/usr/bin/env python3

import chromadb
from pathlib import Path

def check_database():
    print("🔍 Checking ChromaDB database directly...")
    
    # Connect to ChromaDB
    db_path = Path("resume_vectordb")
    client = chromadb.PersistentClient(path=str(db_path))
    
    # Get collections
    collections = client.list_collections()
    print(f"📊 Found {len(collections)} collections")
    
    for collection in collections:
        print(f"\n📂 Collection: {collection.name}")
        count = collection.count()
        print(f"  - Total chunks: {count}")
        
        # Get metadata to count unique documents
        if count > 0:
            results = collection.get(include=["metadatas"], limit=1000)
            if results and results.get("metadatas"):
                unique_sources = set()
                for metadata in results["metadatas"]:
                    if metadata:
                        source = metadata.get("original_file_source") or metadata.get("source")
                        if source:
                            unique_sources.add(source)
                print(f"  - Unique documents: {len(unique_sources)}")
                print(f"  - Sources: {list(unique_sources)}")
            else:
                print("  - No metadata found")

if __name__ == "__main__":
    check_database()