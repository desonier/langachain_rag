#!/usr/bin/env python3
"""
Test script to specifically check the Brandon_Fortt resume for original_file_source field
"""

from query_app import ResumeQuerySystem
import json

def test_fresh_resume():
    """Test the freshly ingested Brandon_Fortt resume for original_file_source field"""
    print("🧪 Testing Fresh Resume for original_file_source Schema Field")
    print("=" * 60)
    
    try:
        # Initialize query system
        query_system = ResumeQuerySystem()
        
        # Search specifically for Brandon Fortt
        docs = query_system.db.similarity_search("Brandon Fortt", k=10)
        
        print(f"📊 Found {len(docs)} documents matching 'Brandon Fortt':")
        print()
        
        fortt_found = False
        
        for i, doc in enumerate(docs, 1):
            if "Fortt" in doc.metadata.get('document_name', ''):
                fortt_found = True
                print(f"✅ FOUND FORTT RESUME #{i}:")
                print(f"   Document: {doc.metadata.get('document_name', 'Unknown')}")
                print(f"   Resume ID: {doc.metadata.get('Resume_ID', 'Unknown')}")
                
                # Check for both fields
                file_path = doc.metadata.get('file_path', 'Not found')
                original_source = doc.metadata.get('original_file_source', 'Not found')
                
                print(f"   file_path: {file_path}")
                print(f"   original_file_source: {original_source}")
                
                # Show all metadata keys to debug
                print(f"   All metadata keys: {list(doc.metadata.keys())}")
                
                # Check if original_file_source exists and is absolute path
                if original_source != 'Not found':
                    print("   ✅ original_file_source field exists!")
                    if original_source.startswith('C:\\') or original_source.startswith('/'):
                        print("   ✅ original_file_source appears to be absolute path")
                    else:
                        print("   ⚠️ original_file_source is not absolute path")
                else:
                    print("   ❌ original_file_source field missing")
                
                print()
        
        if not fortt_found:
            print("❌ No Brandon Fortt resume found - this is unexpected!")
            print("Available documents:")
            for doc in docs[:5]:
                print(f"   - {doc.metadata.get('document_name', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fresh_resume()