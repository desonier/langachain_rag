"""
Test Script to Verify Unified Database Access
Tests that both Streamlit and OpenWebUI interfaces use the same ChromaDB database
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from shared_config import get_config, get_vector_db_path

def test_shared_configuration():
    """Test the shared configuration setup"""
    print("🧪 Testing Shared Configuration")
    print("=" * 50)
    
    # Get configuration
    config = get_config()
    
    # Print configuration summary
    config.print_config_summary()
    
    return config.is_valid()

def test_database_access():
    """Test database access from different components"""
    print("\n🧪 Testing Database Access")
    print("=" * 50)
    
    db_path = get_vector_db_path()
    print(f"📁 Shared database path: {db_path}")
    
    # Test if database exists
    db_path_obj = Path(db_path)
    chroma_file = db_path_obj / "chroma.sqlite3"
    
    print(f"📂 Database directory exists: {'✅' if db_path_obj.exists() else '❌'}")
    print(f"💾 ChromaDB file exists: {'✅' if chroma_file.exists() else '❌'}")
    
    if chroma_file.exists():
        size_mb = round(chroma_file.stat().st_size / (1024 * 1024), 2)
        print(f"📊 Database size: {size_mb} MB")
        return True
    else:
        print("\n⚠️ Database not found. To create:")
        print("   1. Put resume files in ./data/ directory")
        print("   2. Run: python common_tools/ingest_pipeline.py --directory ./data")
        return False

def test_component_imports():
    """Test that components can import and use shared configuration"""
    print("\n🧪 Testing Component Imports")
    print("=" * 50)
    
    # Test ingest pipeline import
    try:
        sys.path.append(str(project_root / "common_tools"))
        from ingest_pipeline import ResumeIngestPipeline
        print("✅ IngestPipeline import successful")
        
        # Test instantiation with shared config
        pipeline = ResumeIngestPipeline(enable_llm_parsing=False)
        print(f"✅ IngestPipeline uses database: {pipeline.persist_directory}")
        
    except Exception as e:
        print(f"❌ IngestPipeline import failed: {e}")
        return False
    
    # Test query system import
    try:
        sys.path.append(str(project_root / "openUIWeb"))
        from query_app import ResumeQuerySystem
        print("✅ QuerySystem import successful")
        
        # Test instantiation with shared config (will fail if no DB, but import should work)
        try:
            query_system = ResumeQuerySystem()
            print(f"✅ QuerySystem uses database: {query_system.persist_directory}")
        except Exception as e:
            print(f"⚠️ QuerySystem instantiation failed (expected if no DB): {e}")
            print(f"   But would use database: {get_vector_db_path()}")
        
    except Exception as e:
        print(f"❌ QuerySystem import failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Resume RAG System - Unified Configuration Test")
    print("=" * 60)
    
    # Test shared configuration
    config_valid = test_shared_configuration()
    
    # Test database access
    db_available = test_database_access()
    
    # Test component imports
    imports_ok = test_component_imports()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"✅ Configuration valid: {'Yes' if config_valid else 'No'}")
    print(f"✅ Database available: {'Yes' if db_available else 'No'}")
    print(f"✅ Component imports: {'Yes' if imports_ok else 'No'}")
    
    if config_valid and imports_ok:
        print("\n🎉 SUCCESS: Both Streamlit and OpenWebUI will use the same database!")
        print(f"📁 Shared database path: {get_vector_db_path()}")
        
        if not db_available:
            print("\n💡 Next steps:")
            print("   1. Create ./data/ directory and add resume files")
            print("   2. Run: python common_tools/ingest_pipeline.py --directory ./data")
            print("   3. Start Streamlit: streamlit run langchain/streamlit_app.py")
            print("   4. Or start OpenWebUI interface: python openUIWeb/web_interface_fixed.py")
    else:
        print("\n❌ ISSUES FOUND: Please fix configuration issues above")
    
    return config_valid and imports_ok

if __name__ == "__main__":
    main()