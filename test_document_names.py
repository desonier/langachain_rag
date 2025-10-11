#!/usr/bin/env python3

from query_app import ResumeQuerySystem

def test_document_names():
    """Test what document names are being returned"""
    
    print("🔍 Testing Document Names in Database")
    print("=" * 50)
    
    query_app = ResumeQuerySystem()
    
    # Get some resumes to check their metadata
    resumes = query_app.list_resumes()
    
    print(f"Found {len(resumes)} resumes:")
    print()
    
    for i, resume in enumerate(resumes[:5]):  # Check first 5
        print(f"📄 Resume {i+1}:")
        print(f"   document_name: '{resume.get('document_name', 'NOT SET')}'")
        print(f"   display_filename: '{resume.get('display_filename', 'NOT SET')}'")
        print(f"   file_path: '{resume.get('file_path', 'NOT SET')}'")
        
        # Check what the Streamlit fix would show
        actual_filename = resume.get('display_filename', '')
        if not actual_filename:
            file_path = resume.get('file_path', '')
            if file_path:
                import os
                actual_filename = os.path.basename(file_path)
            else:
                actual_filename = 'Unknown'
        
        print(f"   🎯 Streamlit would show: '{actual_filename}'")
        print()
    
    # Test ranking query to see what gets returned
    print("🏆 Testing Ranking Query:")
    print("-" * 30)
    
    result = query_app.query_with_ranking('Brandon software engineer', max_resumes=3)
    
    if result.get('ranking_data'):
        for i, candidate in enumerate(result['ranking_data'][:2]):
            print(f"🥇 Candidate {i+1}:")
            print(f"   document_name: '{candidate.get('document_name', 'NOT SET')}'")
            print(f"   display_filename: '{candidate.get('display_filename', 'NOT SET')}'")
            print(f"   candidate_name: '{candidate.get('candidate_name', 'NOT SET')}'")
            print()
    
    print("=" * 50)
    print("🎯 Document name investigation complete!")

if __name__ == "__main__":
    test_document_names()