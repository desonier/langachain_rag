from query_app import ResumeQuerySystem

# Test the enhanced ranking with detailed candidate information
print("🎯 Testing Enhanced Ranking with Candidate Details")
print("=" * 60)

try:
    # Initialize query system
    query_system = ResumeQuerySystem()
    
    # Test ranking query with more focus on candidate details
    test_query = "senior cybersecurity professional with leadership experience"
    print(f"\n🔍 Query: {test_query}")
    
    ranking_results = query_system.query_with_ranking(test_query, max_resumes=2)
    
    if 'error' in ranking_results:
        print(f"❌ Error: {ranking_results['error']}")
    else:
        ranked_resumes = ranking_results.get('ranked_resumes', [])
        total_found = ranking_results.get('total_found', 0)
        
        print(f"\n📊 Found {total_found} relevant resumes, showing top {len(ranked_resumes)}:")
        print("=" * 80)
        
        for i, resume in enumerate(ranked_resumes, 1):
            score = resume.get('relevance_score', 0)
            recommendation = resume.get('recommendation', 'Unknown')
            
            # Enhanced display with all candidate details
            print(f"\n{i}. {'🟢' if score >= 8 else '🟡' if score >= 6 else '🔴'} {resume.get('candidate_name', 'Unknown')} - {recommendation}")
            print(f"   📄 Document: {resume.get('document_name', 'Unknown')}")
            print(f"   📂 Source: {resume.get('file_path', 'Unknown')}")
            print(f"   ⭐ Score: {score}/10")
            print(f"   💼 Experience: {resume.get('experience_years', 0)} years")
            
            # Contact information
            contact = resume.get('contact_info', '')
            if contact:
                print(f"   📞 Contact: {contact}")
            
            # Professional details
            education = resume.get('education', '')
            if education:
                print(f"   🎓 Education: {education}")
            
            job_titles = resume.get('recent_job_titles', '')
            if job_titles:
                print(f"   💼 Recent Roles: {job_titles}")
            
            certs = resume.get('certifications', '')
            if certs:
                print(f"   🏆 Certifications: {certs}")
            
            # Skills summary
            skills = resume.get('key_skills', '')
            if skills:
                skills_list = skills.split(', ')[:4]  # Show first 4 skills
                print(f"   🛠️ Key Skills: {', '.join(skills_list)}")
                if len(skills.split(', ')) > 4:
                    print(f"      ... and {len(skills.split(', ')) - 4} more")
            
            print(f"   🎯 Fit: {resume.get('fit_summary', 'No summary available')}")
            
            # Technical details
            print(f"   📊 Details: {resume.get('matching_chunks', 0)} chunks, {resume.get('parsing_method', 'basic')} processing")
            
            print("   " + "="*70)

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Enhanced ranking test complete!")