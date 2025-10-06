#!/usr/bin/env python3

from query_app import ResumeQuerySystem

def test_query_paths():
    """Test that query shows clean paths"""
    
    print('🔍 QUERY TEST RESULTS:')
    print('=' * 40)
    
    query_app = ResumeQuerySystem()
    result = query_app.query('Brandon')
    
    if result and 'source_documents' in result:
        print(f'Found {len(result["source_documents"])} source documents')
        
        for i, doc in enumerate(result['source_documents'][:3]):
            print(f'📄 Document {i+1}:')
            metadata = doc.metadata
            
            file_path = metadata.get('file_path', '')
            display_filename = metadata.get('display_filename', '')
            
            print(f'   file_path: {file_path}')
            print(f'   display_filename: {display_filename}')
            
            # Check display logic
            if display_filename:
                display_source = f'./data/{display_filename}'
            else:
                display_source = file_path
            
            print(f'   🎯 Display: {display_source}')
            
            if 'tmp' in display_source.lower():
                print('   ❌ TEMP DETECTED')
            else:
                print('   ✅ Clean path')
            print()
    else:
        print('No source documents found')

if __name__ == "__main__":
    test_query_paths()