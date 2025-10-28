#!/usr/bin/env python3

"""
Example: How to update applications to use unified database configuration

This demonstrates how to modify your existing applications to use the
centralized VectorDBConfig to ensure all apps access the same database.
"""

# Standard approach - update your imports
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from vectordb_config import VectorDBConfig, get_standardized_chroma_params

# Load environment variables
load_dotenv()

def example_ingest_pipeline_updated():
    """Example of updated ingest pipeline using unified config"""
    
    print("📥 Example: Updated Ingest Pipeline")
    print("-" * 40)
    
    # ✅ USE UNIFIED CONFIG - All apps will use same path
    persist_directory = VectorDBConfig.DB_DIRECTORY
    print(f"📁 Using standardized database path: {persist_directory}")
    
    # Check database status
    if VectorDBConfig.db_exists():
        print(f"✅ Found existing database (size: {VectorDBConfig.get_db_size():,} bytes)")
    else:
        print("🆕 Will create new database")
    
    # Create embeddings (your existing code)
    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("EMBEDDING_MODEL")
    )
    
    # ✅ USE STANDARDIZED PARAMETERS
    chroma_params = get_standardized_chroma_params(embedding)
    
    # Initialize database with standardized config
    try:
        db = Chroma(**chroma_params)
        print("✅ Database initialized with unified configuration")
        return db
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def example_query_system_updated():
    """Example of updated query system using unified config"""
    
    print("\n🔍 Example: Updated Query System")
    print("-" * 40)
    
    # ✅ USE UNIFIED CONFIG
    persist_directory = VectorDBConfig.DB_DIRECTORY
    print(f"📁 Using standardized database path: {persist_directory}")
    
    # Validate database exists before attempting to load
    if not VectorDBConfig.db_exists():
        print(f"❌ Database not found at: {VectorDBConfig.get_sqlite_file_path()}")
        print("💡 Run ingest pipeline first to create the database")
        return None
    
    print(f"✅ Found database (size: {VectorDBConfig.get_db_size():,} bytes)")
    
    # Create embeddings (your existing code) 
    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("EMBEDDING_MODEL")
    )
    
    # ✅ USE STANDARDIZED PARAMETERS
    chroma_params = get_standardized_chroma_params(embedding)
    
    try:
        db = Chroma(**chroma_params)
        print("✅ Query system loaded with unified configuration")
        return db
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def example_analysis_script_updated():
    """Example of updated analysis script using unified config"""
    
    print("\n📊 Example: Updated Analysis Script") 
    print("-" * 40)
    
    # ✅ USE UNIFIED CONFIG - No more hardcoded paths!
    persist_directory = VectorDBConfig.DB_DIRECTORY
    print(f"📁 Using standardized database path: {persist_directory}")
    
    # Validate configuration before proceeding
    config_status = VectorDBConfig.validate_config()
    
    if not config_status['sqlite_exists']:
        print("❌ No database found - cannot analyze")
        return
    
    print(f"✅ Analyzing database with {config_status['db_size_bytes']:,} bytes")
    
    # Create embeddings
    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("EMBEDDING_MODEL")
    )
    
    # ✅ USE STANDARDIZED PARAMETERS
    chroma_params = get_standardized_chroma_params(embedding)
    
    try:
        db = Chroma(**chroma_params)
        
        # Your analysis logic here
        results = db.similarity_search("", k=10)
        print(f"📈 Found {len(results)} documents in shared database")
        
        return db
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    import os
    
    print("🎯 Demonstrating Unified Database Configuration")
    print("=" * 55)
    
    # Show current configuration status
    VectorDBConfig.print_config_status()
    
    # Run examples (will work if environment is configured)
    try:
        example_ingest_pipeline_updated()
        example_query_system_updated()
        example_analysis_script_updated()
    except Exception as e:
        print(f"\n⚠️  Note: Examples require Azure OpenAI environment configuration")
        print(f"   Error: {e}")
    
    print("\n🎉 Configuration Examples Complete!")
    print("=" * 55)
    print("💡 Benefits of Unified Configuration:")
    print("   ✅ Single source of truth for database paths")
    print("   ✅ Easy to change database location for all apps")
    print("   ✅ Prevents path mismatches between applications")
    print("   ✅ Built-in validation and status checking")
    print("   ✅ Consistent error handling across applications")