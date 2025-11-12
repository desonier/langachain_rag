#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir
sys.path.insert(0, str(project_root))

# Import the admin class
sys.path.append(str(project_root / "common_tools" / "openwebui-resume-rag-admin" / "src"))

from admin.chromadb_admin import ChromaDBAdmin

def main():
    print("🔍 Testing ChromaDB Admin Statistics...")
    
    # Initialize admin
    db_path = project_root / "resume_vectordb"
    admin = ChromaDBAdmin(db_path=db_path)
    
    print(f"📁 Database path: {db_path}")
    
    try:
        stats = admin.get_statistics()
        print("📊 Statistics returned:")
        print(f"  - Total collections: {stats.get('total_collections', 'N/A')}")
        print(f"  - Total items (chunks): {stats.get('total_items', 'N/A')}")
        print(f"  - Total documents: {stats.get('total_documents', 'N/A')}")
        print(f"  - Database size: {stats.get('database_size', 'N/A')}")
        
        if stats.get('collections'):
            print("\n📂 Collection details:")
            for collection in stats['collections']:
                print(f"  - {collection['name']}: {collection.get('count', 'N/A')} chunks, {collection.get('documents', 'N/A')} documents")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()