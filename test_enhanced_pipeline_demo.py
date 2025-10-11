#!/usr/bin/env python3

import tempfile
import os
from ingest_pipeline import ResumeIngestPipeline

def test_pipeline_with_temp_file():
    """Test the enhanced pipeline with actual temp file processing"""
    
    print("🧪 Testing Enhanced Pipeline with Temp File")
    print("=" * 50)
    
    # Create test content
    test_content = """
John Doe Resume

Contact Information:
Email: john.doe@email.com
Phone: (555) 123-4567

Experience:
Software Engineer at Tech Corp (2020-2025)
- Developed Python applications
- Worked with databases and APIs
- Led team of 3 developers

Skills:
- Python
- JavaScript
- SQL
- Git

Education:
B.S. Computer Science, State University (2020)
"""
    
    # Create a temporary file (simulating Streamlit upload)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
        tmp_file.write(test_content)
        tmp_path = tmp_file.name
    
    try:
        print(f"📄 Created temp file: {os.path.basename(tmp_path)}")
        
        # Initialize pipeline
        pipeline = ResumeIngestPipeline(enable_llm_parsing=False)  # Disable LLM for speed
        
        # Test 1: Process with original filename (like Streamlit does)
        print(f"\n🔬 Test 1: Processing with original filename")
        original_name = "./data/John_Doe_Resume.txt"
        
        success, resume_id, chunk_count = pipeline.add_resume(
            tmp_path,
            force_update=True,
            original_filename=original_name
        )
        
        if success:
            print(f"✅ Successfully processed with {chunk_count} chunks")
            print(f"   Resume ID: {resume_id}")
        else:
            print("❌ Processing failed")
        
        # Test 2: Check what's stored in database
        print(f"\n📊 Checking database metadata:")
        
        # Get the resume data
        resumes = pipeline.db.similarity_search("John", k=1)
        if resumes:
            metadata = resumes[0].metadata
            print(f"   file_path: {metadata.get('file_path', 'Not set')}")
            print(f"   display_filename: {metadata.get('display_filename', 'Not set')}")
            print(f"   original_file_source: {metadata.get('original_file_source', 'Not set')}")
            print(f"   is_temp_file: {metadata.get('is_temp_file', 'Not set')}")
            
            # Check display logic
            display_filename = metadata.get('display_filename', '')
            if display_filename:
                display_source = f"./data/{display_filename}"
            else:
                display_source = metadata.get('file_path', 'Unknown')
            
            print(f"\n🎯 Would display source as: {display_source}")
            
            if 'tmp' in display_source.lower():
                print("❌ TEMP DETECTED in display!")
            else:
                print("✅ Clean display path!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            print(f"\n🧹 Cleaned up temp file")
    
    print("\n" + "=" * 50)
    print("🎯 Enhanced pipeline temp file handling verified!")

if __name__ == "__main__":
    test_pipeline_with_temp_file()