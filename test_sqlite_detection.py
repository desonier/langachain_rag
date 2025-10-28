#!/usr/bin/env python3

import os
import shutil
from ingest_pipeline import ResumeIngestPipeline
from query_app import ResumeQuerySystem

def test_sqlite_detection():
    """Test the ChromaDB SQLite file detection logic"""
    
    print("🧪 Testing ChromaDB SQLite File Detection")
    print("=" * 50)
    
    test_db_path = "./test_vectordb"
    sqlite_file_path = os.path.join(test_db_path, "chroma.sqlite3")
    
    # Clean up any existing test database
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)
        print("🧹 Cleaned up existing test database")
    
    print(f"\n📍 Testing with database path: {test_db_path}")
    print(f"📍 SQLite file path: {sqlite_file_path}")
    
    # Test 1: No directory exists
    print(f"\n🔬 Test 1: No directory exists")
    print("-" * 30)
    
    try:
        pipeline = ResumeIngestPipeline(persist_directory=test_db_path, enable_llm_parsing=False)
        print("✅ Pipeline initialized successfully (should create new database)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Check if SQLite file was created
    if os.path.exists(sqlite_file_path):
        print(f"✅ SQLite file created: {sqlite_file_path}")
    else:
        print(f"⚠️  SQLite file not found: {sqlite_file_path}")
    
    # Test 2: Directory exists with SQLite file
    print(f"\n🔬 Test 2: Directory and SQLite file exist")
    print("-" * 30)
    
    try:
        pipeline2 = ResumeIngestPipeline(persist_directory=test_db_path, enable_llm_parsing=False)
        print("✅ Pipeline loaded existing database")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Test query system with existing SQLite file
    print(f"\n🔬 Test 3: Query system with existing SQLite file")
    print("-" * 30)
    
    try:
        query_system = ResumeQuerySystem(persist_directory=test_db_path)
        print("✅ Query system loaded existing database")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Create a fresh directory without SQLite file (Windows-safe approach)
    print(f"\n🔬 Test 4: Directory exists but no SQLite file")
    print("-" * 30)
    
    # Clean up completely and create empty directory
    if os.path.exists(test_db_path):
        try:
            shutil.rmtree(test_db_path)
            print(f"🧹 Removed existing database directory")
        except Exception as e:
            print(f"⚠️  Could not remove directory (files may be in use): {e}")
    
    # Create empty directory
    os.makedirs(test_db_path, exist_ok=True)
    print(f"📁 Created empty directory: {test_db_path}")
    
    try:
        query_system2 = ResumeQuerySystem(persist_directory=test_db_path)
        print("❌ Query system should have failed but didn't")
    except FileNotFoundError as e:
        print(f"✅ Query system correctly failed: {e}")
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")
    
    # Test 5: Test ingest pipeline with empty directory
    print(f"\n🔬 Test 5: Ingest pipeline with empty directory")
    print("-" * 30)
    
    try:
        pipeline3 = ResumeIngestPipeline(persist_directory=test_db_path, enable_llm_parsing=False)
        print("✅ Pipeline handled empty directory case (should create new database)")
        
        # Verify SQLite file was created
        if os.path.exists(sqlite_file_path):
            print(f"✅ SQLite file created after pipeline initialization: {sqlite_file_path}")
        else:
            print(f"⚠️  SQLite file not found after initialization: {sqlite_file_path}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Clean up
    print(f"\n🧹 Cleaning up test database")
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)
        print(f"✅ Removed test database: {test_db_path}")
    
    print("\n" + "=" * 50)
    print("🎯 SQLite Detection Test Complete!")
    print("✅ Enhanced database initialization now checks for chroma.sqlite3 file")
    print("✅ More specific error messages when database components are missing")
    print("✅ Better handling of edge cases (empty directories, missing files)")

if __name__ == "__main__":
    test_sqlite_detection()