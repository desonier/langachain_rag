#!/usr/bin/env python3

import os
import tempfile
import shutil
from ingest_pipeline import ResumeIngestPipeline
from query_app import ResumeQuerySystem

def demo_sqlite_detection():
    """Demonstrate the enhanced ChromaDB SQLite file detection"""
    
    print("🎯 ChromaDB SQLite File Detection Demo")
    print("=" * 45)
    
    # Use a unique temporary directory to avoid file locking issues
    with tempfile.TemporaryDirectory(prefix="vectordb_test_") as temp_dir:
        print(f"📁 Using temporary test directory: {temp_dir}")
        
        sqlite_file = os.path.join(temp_dir, "chroma.sqlite3")
        
        # Scenario 1: Fresh start - no database exists
        print(f"\n📋 Scenario 1: Fresh Database Creation")
        print("-" * 35)
        print(f"Directory exists: {os.path.exists(temp_dir)}")
        print(f"SQLite file exists: {os.path.exists(sqlite_file)}")
        
        print("\n🔧 Creating ingest pipeline...")
        pipeline = ResumeIngestPipeline(persist_directory=temp_dir, enable_llm_parsing=False)
        
        print(f"✅ SQLite file created: {os.path.exists(sqlite_file)}")
        if os.path.exists(sqlite_file):
            size = os.path.getsize(sqlite_file)
            print(f"📊 SQLite file size: {size} bytes")
        
        # Scenario 2: Loading existing database
        print(f"\n📋 Scenario 2: Loading Existing Database")
        print("-" * 35)
        print(f"Directory exists: {os.path.exists(temp_dir)}")
        print(f"SQLite file exists: {os.path.exists(sqlite_file)}")
        
        print("\n🔧 Creating query system...")
        query_system = ResumeQuerySystem(persist_directory=temp_dir)
        print("✅ Successfully loaded existing database")
        
        # Show the directory contents
        print(f"\n📂 Database Directory Contents:")
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                print(f"   📄 {item} ({size} bytes)")
            else:
                print(f"   📁 {item}/")
    
    # Demonstrate error handling for missing database
    print(f"\n📋 Scenario 3: Missing Database Error Handling")
    print("-" * 45)
    
    fake_db_path = "./nonexistent_database"
    print(f"Testing with non-existent path: {fake_db_path}")
    
    try:
        query_system_fail = ResumeQuerySystem(persist_directory=fake_db_path)
        print("❌ Should have failed but didn't")
    except FileNotFoundError as e:
        print(f"✅ Correctly caught missing database: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
    except Exception as e:
        print(f"⚠️  Unexpected error type: {type(e).__name__}: {e}")
    
    print(f"\n🎉 Demo Complete!")
    print("=" * 45)
    print("✅ Enhanced database initialization now:")
    print("   • Specifically checks for chroma.sqlite3 file")
    print("   • Provides clear feedback about database state")
    print("   • Handles edge cases gracefully")
    print("   • Creates new databases when needed")
    print("   • Loads existing databases reliably")

if __name__ == "__main__":
    demo_sqlite_detection()