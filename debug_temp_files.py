#!/usr/bin/env python3

from query_app import ResumeQuerySystem
import json

def debug_temp_files():
    """Debug temp file names in database"""
    
    print("🔍 Debugging Temp File Names in Database")
    print("=" * 50)
    
    # Initialize the system
    query_app = ResumeQuerySystem()
    
    # Test query to see what we get
    result = query_app.query('Brandon')
    
    # Check source documents
    if 'source_documents' in result:
        print('Found source documents:')
        for i, doc in enumerate(result['source_documents'][:5]):
            metadata = doc.metadata
            print(f'\n📄 Doc {i+1}:')
            print(f'  file_path: {metadata.get("file_path", "Not set")}')
            print(f'  display_filename: {metadata.get("display_filename", "Not set")}')
            print(f'  original_file_source: {metadata.get("original_file_source", "Not set")}')
            
            # Check what would be displayed
            display_filename = metadata.get('display_filename', '')
            file_path = metadata.get('file_path', '')
            original_file_source = metadata.get('original_file_source', '')
            
            if display_filename:
                display_source = f"./data/{display_filename}"
            elif original_file_source:
                display_source = original_file_source
            else:
                display_source = file_path
            
            print(f'  🎯 Would display: {display_source}')
            
            # Check for temp patterns
            if 'tmp' in display_source.lower():
                print(f'  ❌ TEMP DETECTED in display source!')
            elif 'tmp' in file_path.lower():
                print(f'  ⚠️  Temp in file_path but not in display')
            else:
                print(f'  ✅ Clean path')
    
    # Also check list of resumes
    print(f'\n📋 Resume List:')
    resumes = query_app.list_resumes()
    
    for i, resume in enumerate(resumes[:5]):
        print(f'\n📄 Resume {i+1}:')
        print(f'  name: {resume.get("name", "Unknown")}')
        print(f'  file_path: {resume.get("file_path", "Not set")}')
        print(f'  display_filename: {resume.get("display_filename", "Not set")}')
        
        # Check for temp names
        file_path = resume.get('file_path', '')
        display_filename = resume.get('display_filename', '')
        
        if 'tmp' in file_path.lower():
            print(f'  ❌ TEMP in file_path: {file_path}')
        if 'tmp' in display_filename.lower():
            print(f'  ❌ TEMP in display_filename: {display_filename}')

if __name__ == "__main__":
    debug_temp_files()