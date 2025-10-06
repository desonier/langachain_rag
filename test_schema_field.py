#!/usr/bin/env python3
"""
Test script to verify the original_file_source field is properly stored in the database
"""

from query_app import ResumeQuerySystem
import json

def test_original_file_source():
    """Test that original_file_source field is properly stored and retrieved"""
    print("🧪 Testing original_file_source Schema Field")
    print("=" * 60)
    
    try:
        # Initialize query system
        query_system = ResumeQuerySystem()
        
        # Get some documents to check their metadata
        docs = query_system.db.similarity_search("Brandon", k=5)
        
        print(f"📊 Checking {len(docs)} documents for original_file_source field:")
        print()
        
        for i, doc in enumerate(docs, 1):
            print(f"{i}. Document: {doc.metadata.get('document_name', 'Unknown')}")
            print(f"   Resume ID: {doc.metadata.get('Resume_ID', 'Unknown')}")
            
            # Check for both fields
            file_path = doc.metadata.get('file_path', 'Not found')
            original_source = doc.metadata.get('original_file_source', 'Not found')
            
            print(f"   file_path: {file_path}")
            print(f"   original_file_source: {original_source}")
            
            # Check if they're different (absolute vs relative path)
            if file_path != original_source:
                print("   ✅ Fields are different (as expected)")
            else:
                print("   ⚠️ Fields are identical")
            
            print()
        
        # Test ranking to see if it uses original_file_source
        print("🎯 Testing ranking display with original_file_source:")
        ranking_results = query_system.query_with_ranking("cybersecurity", max_resumes=1)
        
        if ranking_results['ranked_resumes']:
            resume = ranking_results['ranked_resumes'][0]
            print(f"Resume: {resume.get('candidate_name', 'Unknown')}")
            print(f"file_path: {resume.get('file_path', 'Not found')}")
            print(f"original_file_source: {resume.get('original_file_source', 'Not found')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_original_file_source()