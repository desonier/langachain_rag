import streamlit as st
import os
import sys
import tempfile
import json
from datetime import datetime
from pathlib import Path

# Add the current directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our custom modules
from ingest_pipeline import ResumeIngestPipeline
from query_app import ResumeQuerySystem

# Page configuration
st.set_page_config(
    page_title="Resume RAG System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'ingest_pipeline' not in st.session_state:
    st.session_state.ingest_pipeline = None
if 'query_system' not in st.session_state:
    st.session_state.query_system = None
if 'db_path' not in st.session_state:
    st.session_state.db_path = "./resume_vectordb"

def initialize_ingest_pipeline(db_path, enable_llm):
    """Initialize the ingest pipeline"""
    try:
        if st.session_state.ingest_pipeline is None or st.session_state.db_path != db_path:
            st.session_state.ingest_pipeline = ResumeIngestPipeline(
                persist_directory=db_path,
                enable_llm_parsing=enable_llm
            )
            st.session_state.db_path = db_path
        return True
    except Exception as e:
        st.error(f"Failed to initialize ingest pipeline: {e}")
        return False

def initialize_query_system(db_path):
    """Initialize the query system"""
    try:
        if st.session_state.query_system is None or st.session_state.db_path != db_path:
            st.session_state.query_system = ResumeQuerySystem(persist_directory=db_path)
            st.session_state.db_path = db_path
        return True
    except Exception as e:
        st.error(f"Failed to initialize query system: {e}")
        return False

def ingest_tab():
    """Ingest tab functionality"""
    st.header("📥 Resume Ingest Pipeline")
    st.write("Upload and process resume files into the vector database.")
    
    # Configuration section
    col1, col2 = st.columns(2)
    
    with col1:
        db_path = st.text_input(
            "Database Path", 
            value="./resume_vectordb",
            help="Path where the vector database will be stored"
        )
        
    with col2:
        enable_llm = st.checkbox(
            "Enable LLM-Assisted Parsing",
            value=True,
            help="Use AI to extract structured information (slower but more detailed)"
        )
    
    force_update = st.checkbox(
        "Force Update Existing Resumes",
        value=False,
        help="Update resumes that already exist in the database"
    )
    
    # Initialize pipeline
    if st.button("Initialize Pipeline", type="primary"):
        with st.spinner("Initializing ingest pipeline..."):
            if initialize_ingest_pipeline(db_path, enable_llm):
                st.success("✅ Ingest pipeline initialized successfully!")
                if enable_llm:
                    st.info("🤖 LLM-assisted parsing enabled - processing will be more detailed but slower")
            else:
                return
    
    if st.session_state.ingest_pipeline is None:
        st.warning("⚠️ Please initialize the pipeline first")
        return
    
    st.divider()
    
    # File upload section
    st.subheader("📄 Upload Resume Files")
    
    uploaded_files = st.file_uploader(
        "Choose resume files",
        type=['pdf', 'docx'],
        accept_multiple_files=True,
        help="Upload PDF or DOCX resume files"
    )
    
    if uploaded_files:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"📋 {len(uploaded_files)} file(s) selected:")
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.size:,} bytes)")
        
        with col2:
            if st.button("🚀 Process Files", type="primary"):
                process_uploaded_files(uploaded_files, force_update)
    
    st.divider()
    
    # Database statistics
    st.subheader("📊 Database Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📈 Show Statistics"):
            show_database_stats()
    
    with col2:
        if st.button("📋 List Resumes"):
            list_resumes()

def process_uploaded_files(uploaded_files, force_update):
    """Process uploaded files"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    total_files = len(uploaded_files)
    processed_files = 0
    total_chunks = 0
    
    with results_container:
        st.write("### Processing Results:")
        results_placeholder = st.empty()
        results = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            
            try:
                # Process the file with original filename
                success, resume_id, chunk_count = st.session_state.ingest_pipeline.add_resume(
                    tmp_path, 
                    force_update=force_update,
                    original_filename=f"./data/{uploaded_file.name}"  # Use data directory path
                )
                
                if success:
                    if chunk_count > 0:
                        results.append(f"✅ {uploaded_file.name}: Added {chunk_count} chunks (ID: {resume_id})")
                        total_chunks += chunk_count
                        processed_files += 1
                    else:
                        results.append(f"⏭️ {uploaded_file.name}: Already exists, skipped (ID: {resume_id})")
                else:
                    results.append(f"❌ {uploaded_file.name}: Processing failed")
                
            except Exception as e:
                results.append(f"❌ {uploaded_file.name}: Error - {str(e)}")
            
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
            
            # Update progress
            progress = (i + 1) / total_files
            progress_bar.progress(progress)
            
            # Update results display
            results_placeholder.write("\n".join(results))
        
        status_text.text("✅ Processing complete!")
        
        # Summary
        st.success(f"🎉 Processed {processed_files}/{total_files} files successfully, added {total_chunks} total chunks")

def show_database_stats():
    """Display database statistics"""
    try:
        stats = st.session_state.ingest_pipeline.get_database_stats()
        
        if stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Resumes", stats['total_resumes'])
            
            with col2:
                st.metric("Total Chunks", stats['total_chunks'])
            
            with col3:
                avg_chunks = stats['total_chunks'] / max(stats['total_resumes'], 1)
                st.metric("Avg Chunks/Resume", f"{avg_chunks:.1f}")
            
            st.write("**File Formats:**")
            for format_type, count in stats['file_formats'].items():
                st.write(f"- {format_type}: {count} files")
            
            st.write(f"**Database Path:** `{stats['database_path']}`")
        else:
            st.warning("Could not retrieve database statistics")
            
    except Exception as e:
        st.error(f"Error getting statistics: {e}")

def list_resumes():
    """List all resumes in database"""
    try:
        resumes = st.session_state.ingest_pipeline.list_resumes()
        
        if resumes:
            st.write(f"**Found {len(resumes)} resumes:**")
            
            # Create a table
            import pandas as pd
            
            df_data = []
            for resume in resumes:
                df_data.append({
                    'Document': resume['document_name'],
                    'Format': resume['file_format'],
                    'Chunks': resume['chunk_count'],
                    'Resume ID': resume['resume_id'],
                    'Last Updated': resume['last_updated'][:19] if resume['last_updated'] else 'N/A'
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No resumes found in database")
            
    except Exception as e:
        st.error(f"Error listing resumes: {e}")

def query_tab():
    """Query tab functionality"""
    st.header("🔍 Resume Query System")
    st.write("Search and query resume information from the vector database.")
    
    # Configuration
    db_path = st.text_input(
        "Database Path",
        value="./resume_vectordb",
        help="Path to the vector database to query",
        key="query_db_path"
    )
    
    # Initialize query system
    if st.button("Initialize Query System", type="primary"):
        with st.spinner("Initializing query system..."):
            if initialize_query_system(db_path):
                st.success("✅ Query system initialized successfully!")
                show_database_info()
            else:
                return
    
    if st.session_state.query_system is None:
        st.warning("⚠️ Please initialize the query system first")
        return
    
    st.divider()
    
    # Query interface
    st.subheader("💬 Ask Questions")
    
    # Query input
    query_text = st.text_area(
        "Enter your question:",
        placeholder="e.g., What are Brandon's key skills and technical expertise?",
        height=100
    )
    
    # Query options
    col1, col2 = st.columns(2)
    
    with col1:
        query_type = st.selectbox(
            "Query Type",
            ["All Resumes", "Ranked Candidates", "Specific Resume", "Filter by Format"],
            help="Choose how to scope your search"
        )
    
    with col2:
        if query_type == "Specific Resume":
            resume_id = st.text_input(
                "Resume ID",
                placeholder="Enter resume ID to search",
                help="Find resume IDs in the Ingest tab"
            )
        elif query_type == "Filter by Format":
            file_format = st.selectbox("File Format", ["PDF", "DOCX"])
        elif query_type == "Ranked Candidates":
            max_results = st.slider("Max Results", 1, 10, 5, help="Maximum number of ranked candidates to show")
    
    # Execute query
    if st.button("🔍 Search", type="primary") and query_text:
        with st.spinner("Searching resumes..."):
            execute_query(query_text, query_type, locals())

def execute_query(query_text, query_type, local_vars):
    """Execute the query and display results"""
    try:
        if query_type == "All Resumes":
            # Check if this is a ranking-type query
            ranking_keywords = [
                'top', 'best', 'rank', 'candidates', 'list', 'show me',
                'find me', 'who are', 'which candidates', 'give me'
            ]
            
            is_ranking_query = any(keyword in query_text.lower() for keyword in ranking_keywords)
            
            if is_ranking_query:
                # Extract number if specified (e.g., "top 5", "best 3")
                import re
                number_match = re.search(r'\\b(\\d+)\\b', query_text)
                max_results = int(number_match.group(1)) if number_match else 5
                
                st.info(f"🎯 Detected ranking query - showing top {max_results} candidates")
                ranking_results = st.session_state.query_system.query_with_ranking(query_text, max_results)
                display_ranking_results_streamlit(ranking_results)
            else:
                response = st.session_state.query_system.query(query_text)
                display_standard_results(response)
            
        elif query_type == "Ranked Candidates":
            max_results = local_vars.get('max_results', 5)
            ranking_results = st.session_state.query_system.query_with_ranking(query_text, max_results)
            display_ranking_results_streamlit(ranking_results)
            
        elif query_type == "Specific Resume":
            resume_id = local_vars.get('resume_id')
            if not resume_id:
                st.error("Please enter a Resume ID")
                return
            response = st.session_state.query_system.query(query_text, resume_id=resume_id)
            display_standard_results(response)
            
        elif query_type == "Filter by Format":
            file_format = local_vars.get('file_format')
            response = st.session_state.query_system.search_by_metadata(
                query_text, 
                {"file_format": file_format}
            )
            display_standard_results(response)
        
    except Exception as e:
        st.error(f"Query failed: {e}")

def display_standard_results(response):
    """Display standard query results"""
    # Display results
    st.subheader("📝 Answer")
    st.write(response['result'])
    
    # Display source documents
    if 'source_documents' in response and response['source_documents']:
        st.subheader("📚 Source Documents")
        
        for i, doc in enumerate(response['source_documents'][:3]):  # Show top 3 sources
            with st.expander(f"Source {i+1}: {doc.metadata.get('document_name', 'Unknown')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**Content:**")
                    st.write(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)
                
                with col2:
                    st.write("**Metadata:**")
                    metadata_to_show = {
                        'Document': doc.metadata.get('document_name', 'N/A'),
                        'Section': doc.metadata.get('section_name', 'N/A'),
                        'Format': doc.metadata.get('file_format', 'N/A'),
                        'Source': doc.metadata.get('original_file_source', doc.metadata.get('file_path', 'N/A')),
                        'Chunk Type': doc.metadata.get('chunk_type', 'N/A')
                    }
                    
                    for key, value in metadata_to_show.items():
                        if key == 'Source' and len(str(value)) > 50:
                            # Truncate long file paths for display
                            st.write(f"**{key}:** `...{str(value)[-40:]}`")
                        else:
                            st.write(f"**{key}:** {value}")

def display_ranking_results_streamlit(ranking_results):
    """Display ranked candidate results in Streamlit"""
    if 'error' in ranking_results:
        st.error(f"Ranking failed: {ranking_results['error']}")
        return
    
    ranked_resumes = ranking_results.get('ranked_resumes', [])
    total_found = ranking_results.get('total_found', 0)
    query = ranking_results.get('query', '')
    
    if not ranked_resumes:
        st.warning("No matching candidates found")
        return
    
    st.subheader(f"🎯 Ranked Candidates for: \"{query}\"")
    st.write(f"Found {total_found} relevant resumes, showing top {len(ranked_resumes)} matches:")
    
    for i, resume in enumerate(ranked_resumes, 1):
        score = resume.get('relevance_score', 0)
        recommendation = resume.get('recommendation', 'Unknown')
        
        # Color code based on score
        if score >= 8:
            score_color = "green"
            score_icon = "🟢"
        elif score >= 6:
            score_color = "orange" 
            score_icon = "🟡"
        else:
            score_color = "red"
            score_icon = "🔴"
        
        with st.expander(f"{i}. {score_icon} {resume.get('candidate_name', 'Unknown')} - {recommendation} (Score: {score}/10)", expanded=(i <= 2)):
            # Candidate header with contact info
            st.markdown(f"### 👤 {resume.get('candidate_name', 'Unknown')}")
            
            # Contact information prominently displayed
            contact_info = resume.get('contact_info', '')
            if contact_info:
                st.info(f"📞 **Contact:** {contact_info}")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**🎯 Fit Summary:**")
                st.write(resume.get('fit_summary', 'No summary available'))
                
                # Professional details
                education = resume.get('education', '')
                if education:
                    st.write(f"**🎓 Education:** {education}")
                
                job_titles = resume.get('recent_job_titles', '')
                if job_titles:
                    st.write(f"**💼 Recent Roles:** {job_titles}")
                
                # Key strengths
                strengths = resume.get('key_strengths', [])
                if strengths:
                    st.write("**✅ Key Strengths:**")
                    for strength in strengths:
                        st.write(f"• {strength}")
                
                # Potential concerns
                concerns = resume.get('potential_concerns', [])
                if concerns:
                    st.write("**⚠️ Considerations:**")
                    for concern in concerns:
                        st.write(f"• {concern}")
            
            with col2:
                # Score and basic info
                st.metric("Relevance Score", f"{score}/10")
                st.write(f"**� Experience:** {resume.get('experience_years', 0)} years")
                
                # Resume source information
                st.write("**📂 Resume Source:**")
                st.write(f"• **File:** {resume.get('document_name', 'Unknown')}")
                st.write(f"• **Format:** {resume.get('file_format', 'Unknown')}")
                
                # Use display filename for better source path
                display_source = resume.get('original_file_source', resume.get('file_path', ''))
                if resume.get('display_filename'):
                    display_source = f"./data/{resume.get('display_filename')}"
                    
                if display_source:
                    st.write(f"• **Source:** `{display_source}`")
                
                parsing_method = resume.get('parsing_method', 'basic')
                st.write(f"• **Processing:** {parsing_method}")
                
                # Technical details
                st.write("**📊 Analysis Details:**")
                st.write(f"• **Matching Chunks:** {resume.get('matching_chunks', 0)}")
                st.write(f"• **Skills Count:** {resume.get('skills_count', 0)}")
                st.write(f"• **Certifications Count:** {resume.get('certifications_count', 0)}")
                
                # Last updated
                last_updated = resume.get('last_updated', '')
                if last_updated:
                    try:
                        from datetime import datetime
                        date_obj = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                        st.write(f"• **Last Updated:** {formatted_date}")
                    except:
                        st.write(f"• **Last Updated:** {last_updated[:19]}")
            
            # Skills and certifications in expandable sections
            if resume.get('key_skills') or resume.get('certifications'):
                st.write("---")
                skill_col, cert_col = st.columns(2)
                
                with skill_col:
                    skills = resume.get('key_skills', '')
                    if skills:
                        st.write(f"**🛠️ Complete Skills List:**")
                        skills_list = skills.split(', ')
                        for skill in skills_list:
                            st.write(f"• {skill}")
                
                with cert_col:
                    certs = resume.get('certifications', '')
                    if certs:
                        st.write(f"**🏆 Certifications:**")
                        cert_list = certs.split(', ')
                        for cert in cert_list:
                            st.write(f"• {cert}")
            
            # Source documents section
            source_docs = resume.get('source_documents', [])
            if source_docs:
                st.write("---")
                st.write("**📄 Relevant Resume Sections:**")
                
                for j, doc in enumerate(source_docs[:2]):  # Show top 2 matching sections
                    section_name = doc.metadata.get('section_name', f'Section {j+1}')
                    with st.expander(f"📋 {section_name}", expanded=False):
                        st.write(doc.page_content[:400] + "..." if len(doc.page_content) > 400 else doc.page_content)
                        
                        # Show metadata for this section
                        st.write("**Section Details:**")
                        st.write(f"• **Type:** {doc.metadata.get('chunk_type', 'N/A')}")
                        st.write(f"• **Chunk ID:** {doc.metadata.get('chunk_id', 'N/A')}")
                        if doc.metadata.get('section_order'):
                            st.write(f"• **Order:** {doc.metadata.get('section_order')}")
            
            # Download/view resume button (if file path exists)
            # Try original file path first, then fallback to actual file path
            display_source = f"./data/{resume.get('display_filename')}" if resume.get('display_filename') else None
            actual_file_path = resume.get('file_path', '')
            
            # Determine which file to use for download
            download_path = None
            if display_source and os.path.exists(display_source):
                download_path = display_source
            elif actual_file_path and os.path.exists(actual_file_path):
                download_path = actual_file_path
            
            if download_path:
                st.write("---")
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    # Add download button functionality
                    try:
                        with open(download_path, 'rb') as file:
                            st.download_button(
                                label="📥 Download Resume",
                                data=file,
                                file_name=resume.get('document_name', 'resume'),
                                mime='application/octet-stream'
                            )
                    except Exception as e:
                        st.write(f"📁 Resume: {resume.get('document_name', 'Unknown')}")
                        st.caption(f"Note: File not accessible for download")
                
                with col_btn2:
                    if st.button(f"🔍 View Details {i}", key=f"view_details_{resume.get('resume_id')}"):
                        st.session_state[f"show_details_{i}"] = not st.session_state.get(f"show_details_{i}", False)
                
                with col_btn3:
                    display_name = resume.get('display_filename', resume.get('document_name', 'resume'))
                    st.write(f"📂 `{display_name}`")
        
        # Add some spacing
        if i < len(ranked_resumes):
            st.write("---")

def show_database_info():
    """Show database information in query tab"""
    try:
        resumes = st.session_state.query_system.list_resumes()
        total_chunks = sum(resume['chunk_count'] for resume in resumes)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Resumes", len(resumes))
        
        with col2:
            st.metric("Total Chunks", total_chunks)
        
        with col3:
            formats = {}
            for resume in resumes:
                fmt = resume['file_format']
                formats[fmt] = formats.get(fmt, 0) + 1
            st.metric("File Formats", len(formats))
        
        if resumes:
            st.write("**Available Resumes:**")
            for resume in resumes[:5]:  # Show first 5
                st.write(f"- {resume['document_name']} ({resume['chunk_count']} chunks)")
            
            if len(resumes) > 5:
                st.write(f"... and {len(resumes) - 5} more")
        
    except Exception as e:
        st.error(f"Error getting database info: {e}")

def main():
    """Main Streamlit application"""
    
    # App header
    st.title("📄 Resume RAG System")
    st.write("Upload, process, and query resume documents using AI-powered search")
    
    # Sidebar with configuration
    with st.sidebar:
        st.header("🛠️ Configuration")
        
        # Environment check
        required_env_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_KEY", 
            "AZURE_OPENAI_API_VERSION",
            "EMBEDDING_MODEL",
            "AZURE_OPENAI_CHATGPT_DEPLOYMENT"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            st.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            st.write("Please ensure your .env file is configured properly.")
        else:
            st.success("✅ Environment configured")
        
        st.divider()
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        
        if st.button("🗑️ Clear Database", help="Delete the vector database"):
            if st.session_state.get('confirm_delete'):
                try:
                    import shutil
                    db_path = st.session_state.db_path
                    if os.path.exists(db_path):
                        shutil.rmtree(db_path)
                        st.session_state.ingest_pipeline = None
                        st.session_state.query_system = None
                        st.success("Database cleared!")
                    else:
                        st.info("Database doesn't exist")
                    st.session_state.confirm_delete = False
                except Exception as e:
                    st.error(f"Error clearing database: {e}")
            else:
                st.session_state.confirm_delete = True
                st.warning("Click again to confirm deletion")
        
        # Reset confirmation if user does something else
        if 'confirm_delete' in st.session_state and st.session_state.confirm_delete:
            if st.button("❌ Cancel"):
                st.session_state.confirm_delete = False
    
    # Main tabs
    tab1, tab2 = st.tabs(["📥 Ingest", "🔍 Query"])
    
    with tab1:
        ingest_tab()
    
    with tab2:
        query_tab()
    
    # Footer
    st.divider()
    st.write("---")
    st.caption("💡 Built with Streamlit, LangChain, and Azure OpenAI")

if __name__ == "__main__":
    main()