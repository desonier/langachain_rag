#!/usr/bin/env python3

from ingest_pipeline import ResumeIngestPipeline
import os
import tempfile

def fix_temp_file_names():
    """Fix temp file names in the database by cleaning up and re-ingesting with proper names"""
    
    print("🔧 Fixing Temp File Names in Database")
    print("=" * 50)
    
    # Initialize the pipeline
    ingest_pipeline = ResumeIngestPipeline()
    
    # Get list of resumes to check for temp names
    import chromadb
    from chromadb.config import Settings
    
    # Access the ChromaDB client directly
    client = chromadb.PersistentClient(path="./resume_vectordb")
    collection = client.get_collection("resume_embeddings")
    
    # Get all documents
    all_docs = collection.get()
    
    print(f"Found {len(all_docs['ids'])} documents in database")
    
    # Find documents with temp file names
    temp_docs = []
    proper_docs = []
    
    for i, doc_id in enumerate(all_docs['ids']):
        metadata = all_docs['metadatas'][i]
        file_path = metadata.get('file_path', '')
        display_filename = metadata.get('display_filename', '')
        
        # Check if this has temp names
        is_temp = (
            'tmp' in file_path.lower() or 
            'tmp' in display_filename.lower() or
            'tmp' in doc_id.lower()
        )
        
        if is_temp:
            temp_docs.append({
                'id': doc_id,
                'metadata': metadata,
                'content': all_docs['documents'][i]
            })
        else:
            proper_docs.append({
                'id': doc_id,
                'metadata': metadata
            })
    
    print(f"Found {len(temp_docs)} documents with temp names")
    print(f"Found {len(proper_docs)} documents with proper names")
    
    if temp_docs:
        print("\n🗑️ Documents with temp names:")
        for doc in temp_docs[:5]:  # Show first 5
            metadata = doc['metadata']
            print(f"  • ID: {doc['id']}")
            print(f"    file_path: {metadata.get('file_path', 'Not set')}")
            print(f"    display_filename: {metadata.get('display_filename', 'Not set')}")
            print()
        
        # Ask user if they want to clean these up
        response = input("\n❓ Would you like to remove these temp file entries? (y/N): ")
        
        if response.lower() == 'y':
            print("\n🧹 Cleaning up temp file entries...")
            
            # Delete temp documents
            temp_ids = [doc['id'] for doc in temp_docs]
            collection.delete(ids=temp_ids)
            
            print(f"✅ Removed {len(temp_ids)} temp file entries")
            
            # Optionally re-ingest files from data directory
            data_dir = "./data/"
            if os.path.exists(data_dir):
                files = [f for f in os.listdir(data_dir) if f.endswith(('.pdf', '.docx'))]
                
                if files:
                    print(f"\n📁 Found {len(files)} files in {data_dir}")
                    response = input("❓ Would you like to re-ingest these files with proper names? (y/N): ")
                    
                    if response.lower() == 'y':
                        print("🔄 Re-ingesting files with proper names...")
                        
                        for file in files:
                            file_path = os.path.join(data_dir, file)
                            print(f"  📄 Processing {file}...")
                            
                            try:
                                success, resume_id, chunk_count = ingest_pipeline.add_resume(
                                    file_path,
                                    force_update=True,
                                    original_filename=file_path  # Use the actual file path
                                )
                                
                                if success:
                                    print(f"    ✅ Added {chunk_count} chunks")
                                else:
                                    print(f"    ❌ Failed to process")
                            except Exception as e:
                                print(f"    ❌ Error: {e}")
                        
                        print("✅ Re-ingestion complete!")
            
        else:
            print("ℹ️ No changes made")
    else:
        print("✅ No temp file entries found!")
    
    print("\n" + "=" * 50)
    print("🎯 Database cleanup complete!")

if __name__ == "__main__":
    fix_temp_file_names()