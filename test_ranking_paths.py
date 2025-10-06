#!/usr/bin/env python3

from query_app import ResumeQuerySystem

def test_ranking_paths():
    """Test that ranking query shows clean paths"""
    
    print('🏆 RANKING TEST RESULTS:')
    print('=' * 40)
    
    # Test the ranking query that was showing temp files
    query_app = ResumeQuerySystem()
    result = query_app.query_with_ranking('top 5 Brandon', max_resumes=5)
    
    if result.get('ranking_data'):
        for i, candidate in enumerate(result['ranking_data'][:3]):
            print(f'🥇 Candidate {i+1}: {candidate.get("candidate_name", "Unknown")}')
            
            # Check the source path display
            display_filename = candidate.get('display_filename', '')
            file_path = candidate.get('file_path', '')
            
            if display_filename:
                display_source = f'./data/{display_filename}'
            else:
                display_source = file_path
            
            print(f'   📂 Source: {display_source}')
            
            # Verify no temp files
            if 'tmp' in display_source.lower():
                print('   ❌ TEMP FILE DETECTED!')
            else:
                print('   ✅ Clean path')
            print()
    else:
        print('No ranking data found')

if __name__ == "__main__":
    test_ranking_paths()