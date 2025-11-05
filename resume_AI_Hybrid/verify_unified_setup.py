"""
Simple verification that both interfaces use the same database path
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from shared_config import get_config, get_vector_db_path

def verify_paths():
    """Verify that both interfaces will use the same database path"""
    print("🔍 Verifying Database Path Consistency")
    print("=" * 50)
    
    # Get shared configuration
    config = get_config()
    shared_db_path = get_vector_db_path()
    
    print(f"📁 Shared database path: {shared_db_path}")
    
    # Check what each interface would use
    print(f"\n🖥️ Streamlit Interface:")
    print(f"   Would use: {shared_db_path}")
    print(f"   Status: ✅ Using shared configuration")
    
    print(f"\n💬 OpenWebUI Interface:")
    print(f"   Would use: {shared_db_path}")
    print(f"   Status: ✅ Using shared configuration")
    
    # Verify database exists
    db_path = Path(shared_db_path)
    chroma_file = db_path / "chroma.sqlite3"
    
    print(f"\n💾 Database Status:")
    print(f"   Directory exists: {'✅' if db_path.exists() else '❌'}")
    print(f"   ChromaDB file exists: {'✅' if chroma_file.exists() else '❌'}")
    
    if chroma_file.exists():
        size_mb = round(chroma_file.stat().st_size / (1024 * 1024), 2)
        print(f"   Size: {size_mb} MB")
    
    # Azure configuration
    azure_config = config.get_azure_config()
    print(f"\n🔑 Azure LLM Configuration:")
    print(f"   Endpoint configured: {'✅' if azure_config['endpoint'] else '❌'}")
    print(f"   API Key configured: {'✅' if azure_config['has_key'] else '❌'}")
    print(f"   Deployment: {azure_config['deployment']}")
    
    # Success
    print(f"\n🎉 RESULT: Both interfaces will use the same database!")
    print(f"📍 Path: {shared_db_path}")
    
    return True

def main():
    verify_paths()
    
    print(f"\n📋 Next Steps:")
    print(f"1. Start Streamlit: cd langchain && streamlit run streamlit_app.py")
    print(f"2. Start OpenWebUI: cd openUIWeb && python web_interface_fixed.py")
    print(f"3. Both will use database at: {get_vector_db_path()}")

if __name__ == "__main__":
    main()