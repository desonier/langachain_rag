from query_app import ResumeQuerySystem

# Test the ranking functionality
print("🎯 Testing Enhanced Ranking System")
print("=" * 50)

try:
    # Initialize query system
    query_system = ResumeQuerySystem()
    
    # Test ranking query
    test_query = "cybersecurity professional with penetration testing experience"
    print(f"\n🔍 Query: {test_query}")
    
    ranking_results = query_system.query_with_ranking(test_query, max_resumes=3)
    
    if 'error' in ranking_results:
        print(f"❌ Error: {ranking_results['error']}")
    else:
        ranked_resumes = ranking_results.get('ranked_resumes', [])
        total_found = ranking_results.get('total_found', 0)
        
        print(f"\n📊 Found {total_found} relevant resumes:")
        print("=" * 80)
        
        for i, resume in enumerate(ranked_resumes, 1):
            score = resume.get('relevance_score', 0)
            recommendation = resume.get('recommendation', 'Unknown')
            
            print(f"\n{i}. {resume.get('candidate_name', 'Unknown')} - {recommendation}")
            print(f"   ⭐ Score: {score}/10")
            print(f"   💼 Experience: {resume.get('experience_years', 0)} years")
            print(f"   🎯 {resume.get('fit_summary', 'No summary available')}")
            
            strengths = resume.get('key_strengths', [])
            if strengths:
                print(f"   ✅ Strengths: {', '.join(strengths[:2])}")
            
            concerns = resume.get('potential_concerns', [])
            if concerns:
                print(f"   ⚠️ Considerations: {', '.join(concerns[:1])}")
            
            print("   " + "-" * 60)

except Exception as e:
    print(f"❌ Test failed: {e}")

print("\n✅ Ranking test complete!")