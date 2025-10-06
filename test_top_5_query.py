#!/usr/bin/env python3
"""
Test the top 5 candidates query that was mentioned in the user request
"""

from query_app import ResumeQuerySystem

def test_top_5_query():
    """Test the specific top 5 query mentioned by user"""
    print("🎯 Testing 'Top 5 Candidates' Query")
    print("=" * 60)
    
    try:
        # Use the main database with Brandon resumes
        query_system = ResumeQuerySystem(persist_directory="./resume_vectordb")
        
        # Test the exact query type mentioned by user
        test_query = "top 5 candidates for senior cybersecurity professional with leadership experience"
        
        print(f"🔍 Query: {test_query}")
        print()
        
        # Test detection logic
        ranking_keywords = [
            'top', 'best', 'rank', 'candidates', 'list', 'show me',
            'find me', 'who are', 'which candidates', 'give me'
        ]
        
        is_ranking_query = any(keyword in test_query.lower() for keyword in ranking_keywords)
        
        if is_ranking_query:
            print("✅ Query correctly detected as ranking request")
            
            # Extract number
            import re
            number_match = re.search(r'\\b(\\d+)\\b', test_query)
            max_results = int(number_match.group(1)) if number_match else 5
            
            print(f"🔢 Extracted max_results: {max_results}")
            
            # Execute ranking
            ranking_results = query_system.query_with_ranking(test_query, max_resumes=max_results)
            
            if 'error' in ranking_results:
                print(f"❌ Error: {ranking_results['error']}")
            else:
                ranked_resumes = ranking_results.get('ranked_resumes', [])
                total_found = ranking_results.get('total_found', 0)
                
                print(f"📊 Found {total_found} relevant resumes, showing top {len(ranked_resumes)}:")
                print("=" * 80)
                
                for i, resume in enumerate(ranked_resumes, 1):
                    score = resume.get('relevance_score', 0)
                    recommendation = resume.get('recommendation', 'Unknown')
                    candidate_name = resume.get('candidate_name', 'Unknown')
                    experience = resume.get('experience_years', 0)
                    
                    # Color code based on score
                    if score >= 8:
                        score_icon = "🟢"
                    elif score >= 6:
                        score_icon = "🟡"
                    else:
                        score_icon = "🔴"
                    
                    print(f"\\n{i}. {score_icon} {candidate_name} - {recommendation}")
                    print(f"   ⭐ Score: {score}/10")
                    print(f"   💼 Experience: {experience} years")
                    print(f"   📄 Document: {resume.get('document_name', 'Unknown')}")
                    print(f"   🎯 Summary: {resume.get('fit_summary', 'No summary')[:100]}...")
        else:
            print("❌ Query NOT detected as ranking request")
            
            # Show what would happen with regular query
            response = query_system.query(test_query)
            print(f"📝 Regular query result: {response['result'][:200]}...")
        
        print("\\n" + "=" * 60)
        print("🎉 Top 5 Query Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_top_5_query()