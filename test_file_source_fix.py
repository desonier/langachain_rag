#!/usr/bin/env python3
"""
Test the file source path fix
"""

from ingest_pipeline import ResumeIngestPipeline
from query_app import ResumeQuerySystem
import os

def test_file_source_fix():
    """Test that file sources now show proper paths instead of temp paths"""
    print("📂 Testing File Source Path Fix")
    print("=" * 60)
    
    try:
        # Test ingesting with original filename
        print("📥 Testing Ingest Pipeline with Original Filename:")
        print("-" * 40)
        
        # Initialize ingest pipeline
        ingest_pipeline = ResumeIngestPipeline(enable_llm_parsing=True)
        
        # Test file that exists
        test_file = "./data/Brandon_Tobalski_1-28-2022.pdf"
        if os.path.exists(test_file):
            print(f"✅ Found test file: {test_file}")
            
            # Ingest with explicit original filename
            success, resume_id, chunk_count = ingest_pipeline.add_resume(
                test_file, 
                force_update=True,
                original_filename="./data/Brandon_Tobalski_1-28-2022.pdf"
            )
            
            if success:
                print(f"✅ Successfully ingested with {chunk_count} chunks")
                print(f"📄 Resume ID: {resume_id}")
            else:
                print("❌ Ingestion failed")
        else:
            print(f"⚠️ Test file not found: {test_file}")
        
        print("\\n🔍 Testing Query System Source Display:")
        print("-" * 40)
        
        # Test query system
        query_system = ResumeQuerySystem()
        
        # Test ranking to see source paths
        ranking_results = query_system.query_with_ranking("cybersecurity professional", max_resumes=2)
        
        if ranking_results['ranked_resumes']:
            for i, resume in enumerate(ranking_results['ranked_resumes'], 1):
                candidate_name = resume.get('candidate_name', 'Unknown')
                
                # Check different path fields
                file_path = resume.get('file_path', 'Not found')
                original_source = resume.get('original_file_source', 'Not found')
                display_filename = resume.get('display_filename', 'Not found')
                
                print(f"\\n{i}. Candidate: {candidate_name}")
                print(f"   file_path: {file_path}")
                print(f"   original_file_source: {original_source}")
                print(f"   display_filename: {display_filename}")
                
                # Test display logic
                display_source = original_source
                if display_filename != 'Not found':
                    display_source = f"./data/{display_filename}"
                
                print(f"   Display will show: {display_source}")
                
                # Check if it's showing temp path vs proper path
                if "tmp" in display_source.lower() or "temp" in display_source.lower():
                    print("   ⚠️ Still showing temporary path")
                elif "./data/" in display_source:
                    print("   ✅ Showing proper data directory path")
                else:
                    print("   ℹ️ Showing other path format")
        
        print("\\n" + "=" * 60)
        print("🎉 File Source Path Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_file_source_fix()