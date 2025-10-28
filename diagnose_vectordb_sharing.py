#!/usr/bin/env python3

import os
import chromadb
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma

# Load environment variables
load_dotenv()

def diagnose_vectordb_sharing():
    """Diagnose why two applications might not see each other's ChromaDB data"""
    
    print("🔍 ChromaDB Data Sharing Diagnosis")
    print("=" * 50)
    
    # Check different possible database locations
    possible_locations = [
        "./resume_vectordb",
        "./chroma_store", 
        "./data/vectordb",
        "./vectordb",
        "C:/Users/DamonDesonier/repos/langachain_rag/resume_vectordb",
        "C:/Users/DamonDesonier/repos/langachain_rag/chroma_store"
    ]
    
    print("📂 Checking possible database locations:")
    print("-" * 30)
    
    found_databases = []
    
    for location in possible_locations:
        abs_path = os.path.abspath(location)
        sqlite_file = os.path.join(location, "chroma.sqlite3")
        
        if os.path.exists(location):
            print(f"✅ Directory exists: {abs_path}")
            if os.path.exists(sqlite_file):
                size = os.path.getsize(sqlite_file)
                print(f"   📄 SQLite file: chroma.sqlite3 ({size:,} bytes)")
                found_databases.append((location, abs_path, size))
            else:
                print(f"   ❌ No chroma.sqlite3 file")
                
            # List directory contents
            try:
                contents = os.listdir(location)
                print(f"   📁 Contents: {', '.join(contents)}")
            except:
                pass
        else:
            print(f"❌ Directory not found: {abs_path}")
        print()
    
    if not found_databases:
        print("⚠️  No ChromaDB databases found!")
        return
    
    print(f"🎯 Found {len(found_databases)} database(s)")
    print("=" * 50)
    
    # Create embeddings for testing
    try:
        embedding = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            model=os.getenv("EMBEDDING_MODEL")
        )
        print("✅ Embeddings initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize embeddings: {e}")
        return
    
    # Analyze each database
    for i, (location, abs_path, size) in enumerate(found_databases, 1):
        print(f"\n🔬 Analyzing Database {i}: {location}")
        print("-" * 40)
        
        try:
            # Connect to database
            db = Chroma(
                persist_directory=location,
                embedding_function=embedding
            )
            
            # Get collection info
            collection = db._collection
            collection_name = collection.name
            print(f"📊 Collection name: {collection_name}")
            
            # Get all data
            all_data = collection.get(include=['documents', 'metadatas'])
            total_docs = len(all_data['documents']) if all_data['documents'] else 0
            print(f"📈 Total documents: {total_docs}")
            
            if total_docs > 0:
                # Analyze metadata structure
                metadatas = all_data['metadatas']
                metadata_keys = set()
                resume_ids = set()
                
                for metadata in metadatas:
                    if metadata:
                        metadata_keys.update(metadata.keys())
                        if 'Resume_ID' in metadata:
                            resume_ids.add(metadata['Resume_ID'])
                
                print(f"🏷️  Metadata fields: {sorted(metadata_keys)}")
                print(f"👤 Unique Resume IDs: {len(resume_ids)}")
                
                if resume_ids:
                    print(f"📝 Resume IDs: {sorted(list(resume_ids))}")
                
                # Show sample documents
                print(f"\n📄 Sample documents (first 3):")
                ids = collection.get()['ids']
                for i in range(min(3, len(all_data['documents']))):
                    doc_id = ids[i] if i < len(ids) else f"doc_{i}"
                    content_preview = all_data['documents'][i][:100] + "..." if len(all_data['documents'][i]) > 100 else all_data['documents'][i]
                    metadata = all_data['metadatas'][i]
                    
                    print(f"   ID: {doc_id}")
                    print(f"   Content: {content_preview}")
                    if metadata:
                        print(f"   Metadata: {dict(list(metadata.items())[:3])}...")
                    print()
            
        except Exception as e:
            print(f"❌ Error analyzing database: {e}")
    
    # Check for collection name conflicts
    print(f"\n🔍 Collection Name Analysis")
    print("-" * 30)
    
    collection_names = []
    for location, _, _ in found_databases:
        try:
            db = Chroma(persist_directory=location, embedding_function=embedding)
            collection_names.append((location, db._collection.name))
        except:
            collection_names.append((location, "ERROR"))
    
    for location, name in collection_names:
        print(f"Database: {location} → Collection: {name}")
    
    # Check if collection names are different
    unique_names = set(name for _, name in collection_names if name != "ERROR")
    if len(unique_names) > 1:
        print(f"\n⚠️  ISSUE FOUND: Multiple collection names detected!")
        print(f"   Collection names: {sorted(unique_names)}")
        print(f"   📝 Applications using different collection names won't see each other's data")
    elif len(unique_names) == 1:
        print(f"\n✅ All databases use the same collection name: {list(unique_names)[0]}")
    
    # Summary and recommendations
    print(f"\n💡 Diagnosis Summary & Recommendations")
    print("=" * 50)
    
    if len(found_databases) == 1:
        print("✅ Only one database found - applications should use the same location")
        print(f"   📍 Database location: {found_databases[0][0]}")
        print(f"   🎯 Make sure both applications use this persist_directory")
    elif len(found_databases) > 1:
        print("⚠️  Multiple databases found - applications may be using different locations")
        print("   🎯 Choose ONE database location for both applications")
        print("   📝 Options:")
        for i, (location, abs_path, size) in enumerate(found_databases, 1):
            print(f"      {i}. {location} ({size:,} bytes)")
    
    if len(unique_names) > 1:
        print("\n⚠️  Collection name mismatch detected!")
        print("   🔧 Solutions:")
        print("   1. Specify the same collection_name in both applications")
        print("   2. Or migrate data between collections")
    
    print(f"\n🔧 Quick Fix Commands:")
    print("   # To standardize on ./resume_vectordb:")
    print("   # 1. Update any apps using ./chroma_store to use ./resume_vectordb")
    print("   # 2. Or copy data: cp -r ./chroma_store/* ./resume_vectordb/")

if __name__ == "__main__":
    diagnose_vectordb_sharing()