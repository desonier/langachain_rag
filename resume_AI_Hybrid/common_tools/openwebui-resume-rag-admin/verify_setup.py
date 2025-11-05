"""
Verification script to check if all components are properly set up
"""
import sys
from pathlib import Path

def check_file_structure():
    """Check if all required files and directories exist"""
    print("🔍 Checking file structure...")
    
    base_dir = Path(__file__).parent
    src_dir = base_dir / "src"
    templates_dir = base_dir / "templates"
    tests_dir = base_dir / "tests"
    
    required_files = [
        src_dir / "main.py",
        src_dir / "admin" / "__init__.py",
        src_dir / "admin" / "chromadb_admin.py",
        src_dir / "models" / "__init__.py",
        src_dir / "models" / "admin_models.py",
        src_dir / "models" / "response_models.py",
        templates_dir / "admin_dashboard.html",
        templates_dir / "collection_manager.html",
        templates_dir / "database_manager.html",
        templates_dir / "stats_viewer.html",
        templates_dir / "collection_contents.html",
        tests_dir / "test_response_models.py",
        base_dir / "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(str(file_path))
        else:
            print(f"✅ {file_path.relative_to(base_dir)}")
    
    if missing_files:
        print("\n❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("\n✅ All required files exist!")
    return True

def check_imports():
    """Check if all imports work correctly"""
    print("\n🔍 Checking imports...")
    
    # Add src to path
    src_dir = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_dir))
    
    try:
        # Test Flask imports
        from flask import Flask
        print("✅ Flask imported successfully")
        
        # Test WTForms imports
        from flask_wtf import FlaskForm
        from wtforms import StringField, SelectField
        print("✅ WTForms imported successfully")
        
        # Test ChromaDB import
        import chromadb
        print("✅ ChromaDB imported successfully")
        
        # Test our modules
        from admin.chromadb_admin import ChromaDBAdmin
        print("✅ ChromaDBAdmin imported successfully")
        
        from models.admin_models import CollectionForm, DatabaseForm
        print("✅ Admin models imported successfully")
        
        from models.response_models import CreateResponseModel
        print("✅ Response models imported successfully")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def check_chromadb_init():
    """Test ChromaDB initialization"""
    print("\n🔍 Testing ChromaDB initialization...")
    
    src_dir = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_dir))
    
    try:
        from admin.chromadb_admin import ChromaDBAdmin
        
        # Try to initialize ChromaDB admin
        admin = ChromaDBAdmin()
        print("✅ ChromaDBAdmin initialized successfully")
        
        # Try to get statistics (this will test database connection)
        stats = admin.get_statistics()
        if stats.get('error'):
            print(f"⚠️ Database connection issue: {stats['error']}")
            print("   This is normal if database hasn't been created yet")
        else:
            print("✅ Database connection successful")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB initialization failed: {e}")
        return False

def main():
    """Run all verification checks"""
    print("🚀 ChromaDB Admin Setup Verification")
    print("=" * 50)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Python Imports", check_imports),
        ("ChromaDB Initialization", check_chromadb_init)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! Your ChromaDB Admin is ready to run.")
        print("Run: python src/main.py")
    else:
        print("\n⚠️ Some checks failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())