import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.retrievers.multi_query import MultiQueryRetriever

# Load environment variables from .env file
load_dotenv()

class ResumeQuerySystem:
    """Resume Query System - Queries resumes from vector database"""
    
    def __init__(self, persist_directory="./resume_vectordb"):
        self.persist_directory = persist_directory
        
        # Create embeddings
        self.embedding = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            model=os.getenv("EMBEDDING_MODEL")
        )
        
        # Initialize system
        self._init_system()
    
    def _init_system(self):
        """Initialize vector database and LLM"""
        try:
            # Check if database exists
            if not os.path.exists(self.persist_directory):
                print(f"❌ Database not found at {self.persist_directory}")
                print("💡 Please run the ingest pipeline first to create the database:")
                print("   python ingest_pipeline.py --directory ./data")
                raise FileNotFoundError(f"Database not found: {self.persist_directory}")
            
            # Load database
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding
            )
            print("📂 Loaded resume database successfully")
            
            # Initialize LLM with internet access disabled
            self.llm = AzureChatOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                deployment_name=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT"),
                model_kwargs={
                    "extra_headers": {
                        "ms-azure-ai-chat-enhancements-disable-search": "true"
                    }
                }
            )
            
            # Create RAG chain
            self._create_rag_chain()
            
            # Display database info
            self._display_database_info()
            
        except Exception as e:
            print(f"❌ Error initializing system: {e}")
            raise
    
    def _create_rag_chain(self):
        """Create RAG chain for question answering"""
        try:
            # Enhanced retriever with metadata filtering
            base_retriever = self.db.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 4,
                    "filter": {"content_type": "resume"}
                }
            )
            
            # Multi-query retriever for better semantic search
            self.multi_query_retriever = MultiQueryRetriever.from_llm(
                retriever=base_retriever,
                llm=self.llm
            )
            
            # RAG chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=self.multi_query_retriever,
                return_source_documents=True
            )
            
            print("🔗 RAG chain created successfully")
            
        except Exception as e:
            print(f"⚠️ Error creating RAG chain: {e}")
            # Fallback to simple retriever
            retriever = self.db.as_retriever()
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=retriever,
                return_source_documents=True
            )
    
    def _display_database_info(self):
        """Display information about the loaded database"""
        try:
            resumes = self.list_resumes()
            total_chunks = sum(resume['chunk_count'] for resume in resumes)
            
            print(f"\n📊 Database Information:")
            print(f"   - Total resumes: {len(resumes)}")
            print(f"   - Total chunks: {total_chunks}")
            print(f"   - Database path: {self.persist_directory}")
            
            if resumes:
                print(f"\n📋 Available resumes:")
                for resume in resumes:
                    print(f"   - {resume['document_name']} ({resume['file_format']}): {resume['chunk_count']} chunks")
            
        except Exception as e:
            print(f"⚠️ Could not display database info: {e}")
    
    def query(self, question, resume_id=None):
        """Query the resume database"""
        try:
            if resume_id:
                # Query specific resume
                filtered_retriever = self.db.as_retriever(
                    search_kwargs={
                        "k": 4,
                        "filter": {"Resume_ID": resume_id}
                    }
                )
                qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    retriever=filtered_retriever,
                    return_source_documents=True
                )
                response = qa_chain.invoke({"query": question})
                print(f"🔍 Searched resume {resume_id}")
            else:
                # Query all resumes
                response = self.qa_chain.invoke({"query": question})
                print(f"🔍 Searched all resumes")
            
            return response
            
        except Exception as e:
            print(f"❌ Query error: {e}")
            return {"result": f"Error processing query: {e}", "source_documents": []}
    
    def query_with_ranking(self, question, max_resumes=5):
        """Query database and return ranked resumes with fit explanations"""
        try:
            print(f"🎯 Searching and ranking resumes for: {question}")
            
            # Get relevant documents from all resumes
            docs = self.db.similarity_search(question, k=20)  # Get more docs for ranking
            
            # Group documents by resume
            resume_docs = {}
            for doc in docs:
                resume_id = doc.metadata.get('Resume_ID')
                if resume_id:
                    if resume_id not in resume_docs:
                        resume_docs[resume_id] = []
                    resume_docs[resume_id].append(doc)
            
            if not resume_docs:
                return {
                    "ranked_resumes": [],
                    "total_found": 0,
                    "query": question
                }
            
            # Analyze and rank each resume
            ranked_resumes = []
            
            for resume_id, resume_doc_list in resume_docs.items():
                # Get resume metadata
                first_doc = resume_doc_list[0]
                resume_info = {
                    'resume_id': resume_id,
                    'candidate_name': first_doc.metadata.get('candidate_name', 'Unknown'),
                    'document_name': first_doc.metadata.get('document_name', 'Unknown'),
                    'file_format': first_doc.metadata.get('file_format', 'Unknown'),
                    'file_path': first_doc.metadata.get('file_path', ''),
                    'display_filename': first_doc.metadata.get('display_filename', ''),
                    'contact_info': first_doc.metadata.get('contact_info', ''),
                    'key_skills': first_doc.metadata.get('key_skills', ''),
                    'experience_years': first_doc.metadata.get('experience_years', 0),
                    'certifications': first_doc.metadata.get('certifications', ''),
                    'education': first_doc.metadata.get('education', ''),
                    'recent_job_titles': first_doc.metadata.get('recent_job_titles', ''),
                    'industries': first_doc.metadata.get('industries', ''),
                    'skills_count': first_doc.metadata.get('skills_count', 0),
                    'certifications_count': first_doc.metadata.get('certifications_count', 0),
                    'last_updated': first_doc.metadata.get('last_updated', ''),
                    'parsing_method': first_doc.metadata.get('parsing_method', 'basic'),
                    'matching_chunks': len(resume_doc_list),
                    'top_content': resume_doc_list[0].page_content[:300],
                    'source_documents': resume_doc_list[:3]  # Include source documents for reference
                }
                
                # Generate fit analysis using LLM
                fit_analysis = self._analyze_resume_fit(question, resume_info, resume_doc_list)
                resume_info.update(fit_analysis)
                
                ranked_resumes.append(resume_info)
            
            # Sort by relevance score (descending)
            ranked_resumes.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Limit results
            ranked_resumes = ranked_resumes[:max_resumes]
            
            print(f"📊 Ranked {len(ranked_resumes)} resumes by relevance")
            
            return {
                "ranked_resumes": ranked_resumes,
                "total_found": len(resume_docs),
                "query": question
            }
            
        except Exception as e:
            print(f"❌ Ranking error: {e}")
            return {
                "ranked_resumes": [],
                "total_found": 0,
                "query": question,
                "error": str(e)
            }
    
    def _analyze_resume_fit(self, question, resume_info, resume_docs):
        """Analyze how well a resume fits the query using LLM"""
        try:
            # Combine relevant content from the resume
            combined_content = "\n".join([doc.page_content for doc in resume_docs[:3]])
            
            analysis_prompt = f"""
            Analyze this candidate's qualifications based on their resume content and rate their fit for the requirements: {question}
            
            Candidate: {resume_info.get('candidate_name', 'Unknown')}
            Skills: {resume_info.get('key_skills', 'Not specified')}
            Experience: {resume_info.get('experience_years', 0)} years
            Certifications: {resume_info.get('certifications', 'None listed')}
            Recent Roles: {resume_info.get('recent_job_titles', 'Not specified')}
            
            Resume Content:
            {combined_content[:1500]}
            
            Provide your analysis in this JSON format:
            {{
                "relevance_score": <number 1-10>,
                "fit_summary": "<2-3 sentence summary focusing only on candidate's qualifications and relevant experience>",
                "key_strengths": ["<strength1>", "<strength2>", "<strength3>"],
                "potential_concerns": ["<concern1>", "<concern2>"] or [],
                "recommendation": "<Strong Match|Good Match|Moderate Match|Weak Match>"
            }}
            
            Focus only on:
            - What qualifications this candidate brings
            - Their relevant experience and skills
            - Specific achievements or certifications
            - Leadership or technical expertise demonstrated
            
            Do NOT describe what is being looked for - only describe what the candidate offers.
            
            Score guidelines:
            - 9-10: Exceptional qualifications and experience
            - 7-8: Strong qualifications and experience
            - 5-6: Good qualifications with some gaps
            - 3-4: Moderate qualifications, significant gaps
            - 1-2: Limited relevant qualifications
            
            Return only valid JSON.
            """
            
            response = self.llm.invoke(analysis_prompt)
            
            # Parse JSON response
            import json
            import re
            
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    # Fallback analysis
                    analysis = {
                        "relevance_score": 5,
                        "fit_summary": "Analysis could not be completed, but resume contains relevant information.",
                        "key_strengths": ["Contains relevant content"],
                        "potential_concerns": ["Analysis incomplete"],
                        "recommendation": "Moderate Match"
                    }
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Error in fit analysis: {e}")
            return {
                "relevance_score": 3,
                "fit_summary": f"Could not analyze fit due to error: {str(e)}",
                "key_strengths": ["Resume found in search results"],
                "potential_concerns": ["Analysis incomplete"],
                "recommendation": "Moderate Match"
            }
    
    def search_by_metadata(self, query, metadata_filter=None):
        """Search with optional metadata filtering"""
        try:
            if metadata_filter:
                filtered_retriever = self.db.as_retriever(
                    search_kwargs={
                        "k": 4,
                        "filter": metadata_filter
                    }
                )
                filtered_qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm, 
                    retriever=filtered_retriever,
                    return_source_documents=True
                )
                return filtered_qa_chain.invoke({"query": query})
            else:
                return self.qa_chain.invoke({"query": query})
        except Exception as e:
            print(f"❌ Search error: {e}")
            return {"result": f"Error: {e}", "source_documents": []}
    
    def list_resumes(self):
        """List all resumes in database"""
        try:
            all_docs = self.db.similarity_search("", k=1000)
            
            resume_info = {}
            for doc in all_docs:
                resume_id = doc.metadata.get('Resume_ID')
                if resume_id not in resume_info:
                    resume_info[resume_id] = {
                        'resume_id': resume_id,
                        'document_name': doc.metadata.get('document_name'),
                        'file_format': doc.metadata.get('file_format'),
                        'file_path': doc.metadata.get('file_path'),
                        'last_updated': doc.metadata.get('last_updated'),
                        'chunk_count': 0
                    }
                resume_info[resume_id]['chunk_count'] += 1
            
            return list(resume_info.values())
            
        except Exception as e:
            print(f"❌ Error listing resumes: {e}")
            return []
    
    def get_resume_by_id(self, resume_id):
        """Get specific resume information by ID"""
        try:
            docs = self.db.similarity_search("", k=1000, filter={"Resume_ID": resume_id})
            if not docs:
                return None
            
            resume_info = {
                'resume_id': resume_id,
                'document_name': docs[0].metadata.get('document_name'),
                'file_format': docs[0].metadata.get('file_format'),
                'file_path': docs[0].metadata.get('file_path'),
                'last_updated': docs[0].metadata.get('last_updated'),
                'chunk_count': len(docs),
                'chunks': []
            }
            
            for doc in docs:
                chunk_info = {
                    'chunk_id': doc.metadata.get('chunk_id'),
                    'content': doc.page_content,
                    'chunk_content': doc.metadata.get('chunk_content')
                }
                resume_info['chunks'].append(chunk_info)
            
            return resume_info
            
        except Exception as e:
            print(f"❌ Error getting resume {resume_id}: {e}")
            return None

def interactive_query_session():
    """Run an interactive query session"""
    print("🚀 Resume Query System - Interactive Mode")
    print("=" * 50)
    
    try:
        # Initialize query system
        query_system = ResumeQuerySystem()
        
        print("\n💡 Query Commands:")
        print("   - Type a question to search all resumes")
        print("   - Type 'list' to see available resumes")
        print("   - Type 'resume:<resume_id>' to search a specific resume")
        print("   - Type 'filter:<format>' to search by file format (PDF/DOCX)")
        print("   - Type 'rank:<question>' to get ranked candidates with fit analysis")
        print("   - Type 'exit' or 'quit' to end session")
        
        while True:
            print("\n" + "-" * 50)
            user_input = input("🔍 Enter your query: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break
            
            elif user_input.lower() == 'list':
                resumes = query_system.list_resumes()
                if resumes:
                    print("\n📋 Available resumes:")
                    for resume in resumes:
                        print(f"   - ID: {resume['resume_id']}")
                        print(f"     Name: {resume['document_name']}")
                        print(f"     Format: {resume['file_format']}")
                        print(f"     Chunks: {resume['chunk_count']}")
                        print()
                else:
                    print("❌ No resumes found in database")
            
            elif user_input.startswith('resume:'):
                resume_id = user_input[7:].strip()
                if resume_id:
                    question = input("   Enter question for this resume: ").strip()
                    if question:
                        response = query_system.query(question, resume_id)
                        print(f"\n💬 Answer: {response['result']}")
                        
                        if response['source_documents']:
                            print(f"\n📄 Sources:")
                            for i, doc in enumerate(response['source_documents'][:2]):
                                source_file = doc.metadata.get('document_name', 'Unknown')
                                print(f"   {i+1}. {source_file}: {doc.page_content[:100]}...")
                
            elif user_input.startswith('filter:'):
                file_format = user_input[7:].strip().upper()
                question = input(f"   Enter question for {file_format} resumes: ").strip()
                if question:
                    response = query_system.search_by_metadata(
                        question, 
                        {"file_format": file_format}
                    )
                    print(f"\n💬 Answer: {response['result']}")
            
            elif user_input.startswith('rank:'):
                question = user_input[5:].strip()
                if question:
                    print(f"\n🎯 Ranking resumes for: {question}")
                    ranking_results = query_system.query_with_ranking(question)
                    display_ranking_results(ranking_results)
            
            elif user_input:
                # Check if this is a ranking-type query
                ranking_keywords = [
                    'top', 'best', 'rank', 'candidates', 'list', 'show me',
                    'find me', 'who are', 'which candidates', 'give me'
                ]
                
                is_ranking_query = any(keyword in user_input.lower() for keyword in ranking_keywords)
                
                # Extract number if specified (e.g., "top 5", "best 3")
                import re
                number_match = re.search(r'\b(\d+)\b', user_input)
                max_results = int(number_match.group(1)) if number_match else 5
                
                if is_ranking_query:
                    print(f"\n🎯 Finding top {max_results} candidates for: {user_input}")
                    ranking_results = query_system.query_with_ranking(user_input, max_resumes=max_results)
                    display_ranking_results(ranking_results)
                else:
                    response = query_system.query(user_input)
                    print(f"\n💬 Answer: {response['result']}")
                    
                    if response['source_documents']:
                        print(f"\n📄 Sources:")
                        for i, doc in enumerate(response['source_documents'][:2]):
                            source_file = doc.metadata.get('document_name', 'Unknown')
                            print(f"   {i+1}. {source_file}: {doc.page_content[:100]}...")
            
            else:
                print("❌ Please enter a valid query")
                
    except KeyboardInterrupt:
        print("\n👋 Session interrupted by user")
    except Exception as e:
        print(f"❌ Error in interactive session: {e}")

def display_ranking_results(ranking_results):
    """Display ranked resume results"""
    if 'error' in ranking_results:
        print(f"❌ Error: {ranking_results['error']}")
        return
    
    ranked_resumes = ranking_results.get('ranked_resumes', [])
    total_found = ranking_results.get('total_found', 0)
    
    if not ranked_resumes:
        print("❌ No matching resumes found")
        return
    
    print(f"\n📊 Found {total_found} relevant resumes, showing top {len(ranked_resumes)}:")
    print("=" * 80)
    
    for i, resume in enumerate(ranked_resumes, 1):
        score = resume.get('relevance_score', 0)
        recommendation = resume.get('recommendation', 'Unknown')
        
        # Color code based on score
        if score >= 8:
            score_icon = "🟢"
        elif score >= 6:
            score_icon = "🟡"
        else:
            score_icon = "🔴"
        
        print(f"\n{i}. {score_icon} {resume.get('candidate_name', 'Unknown')} - {recommendation}")
        print(f"   📄 Document: {resume.get('document_name', 'Unknown')}")
        
        # Use original_file_source, but show display filename if available
        display_source = resume.get('original_file_source', resume.get('file_path', 'Unknown'))
        if resume.get('display_filename'):
            display_source = f"./data/{resume.get('display_filename')}"
        print(f"   📂 Source: {display_source}")
        
        print(f"   ⭐ Relevance Score: {score}/10")
        print(f"   💼 Experience: {resume.get('experience_years', 0)} years")
        
        # Contact information
        contact_info = resume.get('contact_info', '')
        if contact_info:
            print(f"   📞 Contact: {contact_info}")
        
        # Education
        education = resume.get('education', '')
        if education:
            print(f"   � Education: {education}")
        
        # Recent job titles
        job_titles = resume.get('recent_job_titles', '')
        if job_titles:
            print(f"   💼 Recent Roles: {job_titles}")
        
        # Certifications
        certifications = resume.get('certifications', '')
        if certifications:
            print(f"   🏆 Certifications: {certifications}")
        
        print(f"   �🎯 {resume.get('fit_summary', 'No summary available')}")
        
        # Key strengths
        strengths = resume.get('key_strengths', [])
        if strengths:
            print(f"   ✅ Key Strengths:")
            for strength in strengths[:3]:
                print(f"      • {strength}")
        
        # Potential concerns
        concerns = resume.get('potential_concerns', [])
        if concerns:
            print(f"   ⚠️ Considerations:")
            for concern in concerns[:2]:
                print(f"      • {concern}")
        
        # Additional details
        print(f"   📊 Resume Details:")
        print(f"      • Format: {resume.get('file_format', 'Unknown')}")
        print(f"      • Skills Count: {resume.get('skills_count', 0)}")
        print(f"      • Certifications Count: {resume.get('certifications_count', 0)}")
        print(f"      • Matching Chunks: {resume.get('matching_chunks', 0)}")
        print(f"      • Processing: {resume.get('parsing_method', 'basic')}")
        
        print("   " + "-" * 60)

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_query_session()
    else:
        print("🚀 Resume Query System")
        print("=" * 30)
        
        try:
            # Initialize and demonstrate basic functionality
            query_system = ResumeQuerySystem()
            
            print("\n💡 Usage examples:")
            print("   # Interactive mode:")
            print("   python query_app.py --interactive")
            print("   ")
            print("   # In Python:")
            print("   from query_app import ResumeQuerySystem")
            print("   query_system = ResumeQuerySystem()")
            print("   response = query_system.query('What skills does this person have?')")
            print("   print(response['result'])")
            
        except Exception as e:
            print(f"❌ Could not initialize system: {e}")
            print("💡 Make sure to run the ingest pipeline first:")
            print("   python ingest_pipeline.py --directory ./data")

if __name__ == "__main__":
    main()