#!/usr/bin/env python3
"""
Interactive test to demonstrate the corrected top 5 candidates functionality
"""

from query_app import ResumeQuerySystem

def demo_interactive_fix():
    """Demonstrate the fix for the top 5 candidates issue"""
    print("🎯 Interactive Top 5 Candidates Demo")
    print("=" * 60)
    print("This demonstrates the fix for getting structured candidate ranking")
    print("instead of narrative responses when asking for 'top 5 candidates'")
    print()
    
    try:
        # Initialize with the correct database
        query_system = ResumeQuerySystem(persist_directory="./resume_vectordb")
        
        # Simulate the user's original query
        user_query = "top 5 candidates for senior cybersecurity professional with leadership experience"
        
        print(f"🔍 Original Query: \"{user_query}\"")
        print()
        
        print("🤖 BEFORE FIX (what you experienced):")
        print("   - System used regular query() method")
        print("   - Generated narrative response listing candidates")
        print("   - No scores, contact info, or structured data")
        print()
        
        print("✅ AFTER FIX (what happens now):")
        print("   - System detects 'top' + 'candidates' keywords")
        print("   - Automatically uses query_with_ranking() method")
        print("   - Extracts '5' as max_results parameter")
        print("   - Returns structured candidate data with scores")
        print()
        
        # Test the detection logic
        ranking_keywords = ['top', 'best', 'rank', 'candidates', 'list', 'show me', 'find me', 'who are', 'which candidates', 'give me']
        is_ranking_query = any(keyword in user_query.lower() for keyword in ranking_keywords)
        
        import re
        number_match = re.search(r'\\b(\\d+)\\b', user_query)
        max_results = int(number_match.group(1)) if number_match else 5
        
        print(f"🔍 Detection Results:")
        print(f"   - Contains ranking keywords: {is_ranking_query}")
        print(f"   - Extracted number: {max_results}")
        print()
        
        if is_ranking_query:
            print("📊 Executing Ranking Query...")
            ranking_results = query_system.query_with_ranking(user_query, max_resumes=max_results)
            
            ranked_resumes = ranking_results.get('ranked_resumes', [])
            total_found = ranking_results.get('total_found', 0)
            
            print(f"\\n✅ SUCCESS: Found {total_found} relevant resumes, showing top {len(ranked_resumes)}:")
            print("=" * 70)
            
            for i, resume in enumerate(ranked_resumes, 1):
                score = resume.get('relevance_score', 0)
                candidate_name = resume.get('candidate_name', 'Unknown')
                contact = resume.get('contact_info', 'Not available')
                experience = resume.get('experience_years', 0)
                skills = resume.get('key_skills', 'Not specified')
                
                print(f"\\n{i}. {candidate_name}")
                print(f"   📧 Contact: {contact[:50]}...")
                print(f"   ⭐ Score: {score}/10")
                print(f"   💼 Experience: {experience} years")
                print(f"   🛠️ Key Skills: {skills[:60]}...")
            
            print("\\n" + "=" * 70)
            print("🎉 Now you get structured candidate data instead of narrative!")
        
        print("\\n📋 Usage Instructions:")
        print("   - In Interactive Mode: Just type 'top 5 cybersecurity professionals'")
        print("   - In Streamlit: Use 'All Resumes' query type (auto-detects) or 'Ranked Candidates'")
        print("   - Keywords that trigger ranking: top, best, candidates, list, show me, find me")
        print("   - Numbers are auto-extracted: 'top 3', 'best 5', 'show me 10', etc.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_interactive_fix()