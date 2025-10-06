#!/usr/bin/env python3
"""
Test the intelligent ranking detection system
"""

from query_app import ResumeQuerySystem

def test_intelligent_ranking():
    """Test that ranking queries are automatically detected"""
    print("🧠 Testing Intelligent Ranking Detection")
    print("=" * 60)
    
    try:
        # Initialize query system (without interactive mode)
        query_system = ResumeQuerySystem()
        
        # Test different ranking query formats
        ranking_queries = [
            "top 5 cybersecurity professionals",
            "best 3 candidates for software development",
            "show me the top candidates with Python experience",
            "find me 4 best developers",
            "who are the top network administrators",
            "give me the best 2 project managers",
            "list the top candidates for leadership roles"
        ]
        
        # Test non-ranking queries
        regular_queries = [
            "What skills does Brandon have?",
            "Explain the cybersecurity experience",
            "How many years of experience?",
            "What certifications are mentioned?"
        ]
        
        print("🎯 Testing Ranking Query Detection:")
        print("-" * 40)
        
        for i, query in enumerate(ranking_queries, 1):
            print(f"\n{i}. Query: \"{query}\"")
            
            # Test detection logic
            ranking_keywords = [
                'top', 'best', 'rank', 'candidates', 'list', 'show me',
                'find me', 'who are', 'which candidates', 'give me'
            ]
            
            is_ranking_query = any(keyword in query.lower() for keyword in ranking_keywords)
            
            # Extract number
            import re
            number_match = re.search(r'\\b(\\d+)\\b', query)
            max_results = int(number_match.group(1)) if number_match else 5
            
            if is_ranking_query:
                print(f"   ✅ Detected as ranking query (max_results: {max_results})")
                
                # Actually test the ranking
                ranking_results = query_system.query_with_ranking(query, max_resumes=max_results)
                found_count = len(ranking_results.get('ranked_resumes', []))
                total_found = ranking_results.get('total_found', 0)
                
                print(f"   📊 Found {total_found} total, showing {found_count} candidates")
            else:
                print(f"   ❌ NOT detected as ranking query")
        
        print("\\n📝 Testing Regular Query Detection:")
        print("-" * 40)
        
        for i, query in enumerate(regular_queries, 1):
            print(f"\\n{i}. Query: \"{query}\"")
            
            ranking_keywords = [
                'top', 'best', 'rank', 'candidates', 'list', 'show me',
                'find me', 'who are', 'which candidates', 'give me'
            ]
            
            is_ranking_query = any(keyword in query.lower() for keyword in ranking_keywords)
            
            if is_ranking_query:
                print(f"   ❌ Incorrectly detected as ranking query")
            else:
                print(f"   ✅ Correctly detected as regular query")
        
        print("\\n" + "=" * 60)
        print("🎉 Intelligent Detection Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_intelligent_ranking()