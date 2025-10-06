#!/usr/bin/env python3
"""
Test the updated qualification-focused ranking analysis with different queries
"""

from query_app import ResumeQuerySystem

def test_qualification_focus():
    """Test that analysis focuses on candidate qualifications, not query description"""
    print("🎯 Testing Qualification-Focused Analysis")
    print("=" * 60)
    
    try:
        # Initialize query system
        query_system = ResumeQuerySystem()
        
        # Test different types of queries
        test_queries = [
            "software developer with Python experience",
            "project manager with agile methodology",
            "data analyst with SQL skills",
            "network administrator with security clearance"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test Query {i}: {query}")
            print("-" * 50)
            
            ranking_results = query_system.query_with_ranking(query, max_resumes=1)
            
            if ranking_results['ranked_resumes']:
                resume = ranking_results['ranked_resumes'][0]
                candidate_name = resume.get('candidate_name', 'Unknown')
                fit_summary = resume.get('fit_summary', 'No summary available')
                score = resume.get('relevance_score', 0)
                
                print(f"👤 Candidate: {candidate_name}")
                print(f"⭐ Score: {score}/10")
                print(f"🎯 Analysis: {fit_summary}")
                
                # Check if the analysis avoids describing the query
                query_words = query.lower().split()
                fit_lower = fit_summary.lower()
                
                # Look for patterns that indicate query description vs qualification focus
                qualification_indicators = [
                    "experience in", "background in", "specializes in", "demonstrates",
                    "skilled in", "certified in", "expertise in", "proven", "accomplished"
                ]
                
                query_description_indicators = [
                    "looking for", "seeking", "requires", "needs", "position calls for",
                    "role demands", "job requires"
                ]
                
                has_qualification_focus = any(indicator in fit_lower for indicator in qualification_indicators)
                has_query_description = any(indicator in fit_lower for indicator in query_description_indicators)
                
                if has_qualification_focus and not has_query_description:
                    print("✅ Analysis properly focuses on candidate qualifications")
                elif has_query_description:
                    print("⚠️ Analysis includes query description (should focus on candidate)")
                else:
                    print("ℹ️ Analysis format acceptable")
                
            else:
                print("❌ No candidates found for this query")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qualification_focus()