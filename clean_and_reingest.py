#!/usr/bin/env python3

import os
import shutil
from ingest_pipeline import ResumeIngestPipeline

def clean_and_reingest():
    """Clean database and re-ingest all files from data directory with proper names"""
    
    print("🔧 Cleaning Database and Re-ingesting Files")
    print("=" * 50)
    
    # Check what files exist in data directory
    data_dir = "./data/"
    if not os.path.exists(data_dir):
        print(f"❌ Data directory {data_dir} not found!")
        return
    
    files = [f for f in os.listdir(data_dir) if f.endswith(('.pdf', '.docx'))]
    
    if not files:
        print(f"❌ No resume files found in {data_dir}")
        return
    
    print(f"📁 Found {len(files)} files in {data_dir}:")
    for file in files:
        print(f"  • {file}")
    
    # Ask user for confirmation
    response = input(f"\n❓ This will delete the current database and re-ingest all {len(files)} files. Continue? (y/N): ")
    
    if response.lower() != 'y':
        print("ℹ️ Operation cancelled")
        return
    
    # Remove existing database
    db_path = "./resume_vectordb"
    if os.path.exists(db_path):
        print(f"🗑️ Removing existing database at {db_path}...")
        shutil.rmtree(db_path)
        print("✅ Database removed")
    
    # Initialize new pipeline
    print("🚀 Initializing new ingest pipeline...")
    ingest_pipeline = ResumeIngestPipeline(enable_llm_parsing=True)
    
    # Ingest each file with proper naming
    print("📄 Processing files...")
    total_chunks = 0
    successful_files = 0
    
    for file in files:
        file_path = os.path.join(data_dir, file)
        print(f"\n  📄 Processing {file}...")
        
        try:
            # Use the file path directly - this ensures proper naming
            success, resume_id, chunk_count = ingest_pipeline.add_resume(
                file_path,
                force_update=False,
                original_filename=file_path  # This will ensure proper display name
            )
            
            if success:
                total_chunks += chunk_count
                successful_files += 1
                print(f"    ✅ Added {chunk_count} chunks (ID: {resume_id})")
            else:
                print(f"    ❌ Failed to process")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print(f"\n" + "=" * 50)
    print("📊 INGESTION COMPLETE:")
    print(f"✅ Successfully processed: {successful_files}/{len(files)} files")
    print(f"📝 Total chunks created: {total_chunks}")
    print("🎯 All files should now have proper './data/filename.ext' paths!")

if __name__ == "__main__":
    clean_and_reingest()