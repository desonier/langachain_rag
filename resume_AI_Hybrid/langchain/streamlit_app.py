import streamlit as st
import os
import sys
import tempfile
import json
from datetime import datetime
from pathlib import Path

# Add the parent directory to the Python path so we can import shared modules
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

# Import shared configuration
from shared_config import get_config, get_vector_db_path

# Import our custom modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common_tools'))
from ingest_pipeline import ResumeIngestPipeline

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'openUIWeb'))
from query_app import ResumeQuerySystem

# Page configuration
st.set_page_config(
    page_title="Resume RAG System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state with shared configuration
if 'ingest_pipeline' not in st.session_state:
    st.session_state.ingest_pipeline = None
if 'query_system' not in st.session_state:
    st.session_state.query_system = None
if 'current_collection' not in st.session_state:
    st.session_state.current_collection = None
if 'db_path' not in st.session_state:
    # Use shared configuration for consistent database path
    st.session_state.db_path = get_vector_db_path()

# Load shared configuration for display
config = get_config()

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

def initialize_query_system(db_path, collection_name=None):
    """Initialize the query system with shared configuration"""
    try:
        if st.session_state.query_system is None or st.session_state.db_path != db_path:
            st.session_state.query_system = ResumeQuerySystem(persist_directory=db_path, collection_name=collection_name)
            st.session_state.db_path = db_path
            st.session_state.current_collection = collection_name
        return True
    except Exception as e:
        st.error(f"Failed to initialize query system: {e}")
        return False

def get_available_collections(db_path):
    """Get list of available collections from ChromaDB using factory"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from chromadb_factory import list_collections
        
        collections = list_collections(db_path)
        return collections if collections else []
    except Exception as e:
        st.error(f"Error getting collections: {e}")
        return []

def ingest_tab():
    """Ingest tab functionality"""
    st.header("📥 Resume Ingest Pipeline")
    st.write("Upload and process resume files into the vector database.")
    
    # Configuration section
    col1, col2 = st.columns(2)
    
    with col1:
        db_path = st.text_input(
            "Database Path", 
            value=st.session_state.db_path,  # Use shared configuration
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
                # Debug: Show what filename we're passing
                st.write(f"🔍 Debug: Processing '{uploaded_file.name}' (size: {uploaded_file.size} bytes)")
                
                # Process the file with original filename preserved
                success, resume_id, chunk_count = st.session_state.ingest_pipeline.add_resume(
                    tmp_path, 
                    force_update=force_update,
                    original_filename=uploaded_file.name  # Keep the original filename
                )
                
                # Debug: Show the generated Resume_ID
                st.write(f"🔍 Debug: Generated Resume_ID: {resume_id}")
                
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
        
        # Enhanced Summary with detailed stats
        st.success(f"🎉 Upload Complete! Processed {processed_files}/{total_files} files successfully")
        
        # Show detailed results
        if processed_files > 0:
            st.info(f"📊 Added {total_chunks} total chunks to the database")
            
            # Get updated database stats
            try:
                updated_stats = st.session_state.ingest_pipeline.get_database_stats()
                if updated_stats:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📄 Total Resumes", updated_stats['total_resumes'])
                    with col2:
                        st.metric("📦 Total Chunks", updated_stats['total_chunks'])
                    with col3:
                        st.metric("📁 New Files", processed_files)
                    with col4:
                        st.metric("📈 New Chunks", total_chunks)
                        
                    st.success("✅ Database updated successfully! Switch to the Query tab to search your resumes.")
            except Exception as e:
                st.warning(f"Could not fetch updated stats: {e}")
        
        if processed_files < total_files:
            failed_count = total_files - processed_files
            st.warning(f"⚠️ {failed_count} file(s) failed to process. Check the details above.")

def show_database_stats():
    """Display enhanced database statistics in ingest tab"""
    try:
        stats = st.session_state.ingest_pipeline.get_database_stats()
        
        if stats and stats['total_resumes'] > 0:
            st.subheader("📊 Current Database Status")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 Total Resumes", stats['total_resumes'])
            
            with col2:
                st.metric("📦 Total Chunks", stats['total_chunks'])
            
            with col3:
                avg_chunks = stats['total_chunks'] / stats['total_resumes'] if stats['total_resumes'] > 0 else 0
                st.metric("📈 Avg Chunks/Resume", f"{avg_chunks:.1f}")
                
            with col4:
                # Get database size
                import os
                db_path = st.session_state.db_path
                try:
                    if os.path.exists(db_path):
                        size_mb = os.path.getsize(db_path) / (1024 * 1024)
                        st.metric("💾 DB Size", f"{size_mb:.1f} MB")
                    else:
                        st.metric("💾 DB Size", "0 MB")
                except:
                    st.metric("💾 DB Size", "Unknown")
            
            # Show recent uploads info
            try:
                # Get list of resume document names if available
                resumes = st.session_state.ingest_pipeline.list_resumes()
                if resumes:
                    with st.expander(f"📋 View All {len(resumes)} Resumes", expanded=False):
                        for i, resume in enumerate(resumes[:10]):  # Show first 10
                            st.write(f"{i+1}. **{resume['document_name']}** ({resume['chunk_count']} chunks)")
                        if len(resumes) > 10:
                            st.write(f"... and {len(resumes) - 10} more resumes")
            except:
                pass  # Skip if method not available
                
        else:
            st.info("📭 No resumes in database yet. Upload some files to get started!")
            
    except Exception as e:
        st.warning(f"Could not load database statistics: {e}")

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
    
    # Configuration section
    st.subheader("⚙️ Configuration")
    st.write("Set up your database connection and select which collection to query.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        db_path = st.text_input(
            "Database Path",
            value=st.session_state.db_path,  # Use shared configuration
            help="Path to the vector database to query",
            key="query_db_path"
        )
    
    with col2:
        # Get available collections
        available_collections = []
        if os.path.exists(db_path):
            available_collections = get_available_collections(db_path)
        
        # Collection selection
        if available_collections:
            collection_options = ["(Default Collection)"] + available_collections
            selected_collection = st.selectbox(
                "Select Collection",
                options=collection_options,
                index=0,
                help="Choose which collection to query from. Each collection may contain different types or sets of documents.",
                key="selected_collection"
            )
            
            # Convert selection to actual collection name
            collection_name = None if selected_collection == "(Default Collection)" else selected_collection
            
            # Show collection info
            if collection_name:
                st.info(f"🎯 **Selected:** {collection_name}")
            else:
                st.info("🎯 **Selected:** Default Collection")
        else:
            st.warning("⚠️ No collections found. Initialize the query system to see available collections.")
            collection_name = None
    
    # Initialize query system
    init_col1, init_col2 = st.columns([2, 1])
    
    with init_col1:
        if st.button("Initialize Query System", type="primary"):
            with st.spinner("Initializing query system..."):
                if initialize_query_system(db_path, collection_name):
                    if collection_name:
                        st.success(f"✅ Query system initialized successfully with collection: {collection_name}")
                    else:
                        st.success("✅ Query system initialized successfully with default collection!")
                    st.rerun()  # Refresh to show database info
                else:
                    return
    
    with init_col2:
        if st.button("🔄 Refresh Collections", help="Refresh the list of available collections"):
            st.rerun()
    
    if st.session_state.query_system is None:
        st.warning("⚠️ Please initialize the query system first")
        
        # Show available collections info if any
        if available_collections:
            st.info(f"📂 Found {len(available_collections)} collections: {', '.join(available_collections)}")
        return
    
    # Show current collection info
    current_collection = getattr(st.session_state, 'current_collection', None)
    if current_collection:
        st.info(f"🎯 Currently querying collection: **{current_collection}**")
    else:
        st.info("🎯 Currently querying: **Default Collection**")
    
    # Show database information when system is ready
    st.divider()
    st.subheader("📊 Database Overview")
    show_database_info()
    
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
                help="Find resume IDs in the database overview above"
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
                
                # Display actual filename from display_filename or extract from file_path
                actual_filename = resume.get('display_filename', '')
                if not actual_filename:
                    file_path = resume.get('file_path', '')
                    if file_path:
                        actual_filename = os.path.basename(file_path)
                    else:
                        actual_filename = 'Unknown'
                
                st.write(f"• **File:** {actual_filename}")
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
            
            # Source documents section - enhanced and more prominent
            source_docs = resume.get('source_documents', [])
            if source_docs:
                st.write("---")
                st.write("**📄 Source Document Sections**")
                st.caption(f"Showing {len(source_docs[:3])} most relevant sections from this resume")
                
                for j, doc in enumerate(source_docs[:3]):  # Show top 3 matching sections
                    section_name = doc.metadata.get('section_name', f'Section {j+1}')
                    chunk_type = doc.metadata.get('chunk_type', 'Content')
                    
                    # Create a more descriptive title for the expander
                    expander_title = f"📋 {section_name}"
                    if chunk_type and chunk_type != 'Content':
                        expander_title += f" ({chunk_type})"
                    
                    with st.expander(expander_title, expanded=(j == 0)):  # Expand first section by default
                        # Show the content with better formatting
                        content = doc.page_content.strip()
                        if len(content) > 800:
                            content = content[:800] + "..."
                        
                        st.markdown(f"```\n{content}\n```")
                        
                        # Show metadata for this section in a compact way
                        meta_col1, meta_col2 = st.columns(2)
                        with meta_col1:
                            st.caption(f"📍 **Section:** {section_name}")
                            if doc.metadata.get('section_order'):
                                st.caption(f"🔢 **Order:** #{doc.metadata.get('section_order')}")
                        with meta_col2:
                            st.caption(f"📂 **Chunk ID:** {doc.metadata.get('chunk_id', 'N/A')}")
                            st.caption(f"📄 **Type:** {chunk_type}")
            else:
                st.write("---")
                st.info("📄 No specific source sections available for this resume")
            
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
    """Show enhanced database information in query tab"""
    try:
        # Show current collection info
        current_collection = getattr(st.session_state, 'current_collection', None)
        if current_collection:
            st.info(f"📂 **Current Collection:** {current_collection}")
        else:
            st.info("📂 **Current Collection:** Default Collection")
        
        # Show available collections
        db_path = st.session_state.db_path
        available_collections = get_available_collections(db_path)
        if available_collections:
            with st.expander(f"📁 Available Collections ({len(available_collections)})", expanded=False):
                cols = st.columns(min(len(available_collections), 4))
                for i, collection in enumerate(available_collections):
                    with cols[i % 4]:
                        if collection == current_collection:
                            st.success(f"🎯 **{collection}** (active)")
                        else:
                            st.write(f"📂 {collection}")
        
        resumes = st.session_state.query_system.list_resumes()
        total_chunks = sum(resume['chunk_count'] for resume in resumes)
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
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
            
        with col4:
            avg_chunks = total_chunks / len(resumes) if resumes else 0
            st.metric("Avg Chunks/Resume", f"{avg_chunks:.1f}")
        
        # Detailed breakdown
        if resumes:
            st.subheader("📋 Resume Details")
            
            # Show format breakdown
            if formats:
                st.write("**File Format Distribution:**")
                format_cols = st.columns(len(formats))
                for i, (fmt, count) in enumerate(formats.items()):
                    with format_cols[i]:
                        st.metric(f"{fmt} Files", count)
            
            # Resume list with expandable details
            st.write("**Available Resumes:**")
            
            # Sort resumes by chunk count for better visibility
            sorted_resumes = sorted(resumes, key=lambda x: x['chunk_count'], reverse=True)
            
            for i, resume in enumerate(sorted_resumes):
                with st.expander(f"📄 {resume['document_name']} ({resume['chunk_count']} chunks)", expanded=(i < 3)):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Resume ID:** `{resume['resume_id']}`")
                        st.write(f"**File Format:** {resume['file_format']}")
                    with col_b:
                        st.write(f"**Chunk Count:** {resume['chunk_count']}")
                        if 'file_size' in resume:
                            st.write(f"**File Size:** {resume.get('file_size', 'Unknown')}")
                    
                    # Show sample chunk preview if available
                    try:
                        sample_chunks = st.session_state.query_system.get_resume_chunks(resume['resume_id'], limit=1)
                        if sample_chunks:
                            st.write("**Sample Content:**")
                            st.text(sample_chunks[0]['content'][:200] + "..." if len(sample_chunks[0]['content']) > 200 else sample_chunks[0]['content'])
                    except:
                        pass
        else:
            st.info("📭 No resumes found in database. Use the Ingest tab to upload some resumes!")
        
    except Exception as e:
        st.error(f"Error getting database info: {e}")
        st.write("Please make sure the query system is initialized.")

def main():
    """Main Streamlit application"""
    
    # App header
    st.title("📄 Resume RAG System")
    st.write("Upload, process, and query resume documents using AI-powered search")
    
    # Sidebar with configuration
    with st.sidebar:
        st.header("🛠️ Configuration")
        
        # Environment check using shared configuration
        azure_config = config.get_azure_config()
        db_info = config.get_database_info()
        
        if config.is_valid():
            st.success("✅ Environment configured")
            st.write(f"📁 Database: {db_info['path']}")
            st.write(f"💾 DB Exists: {'✅' if db_info['exists'] else '❌'}")
            if db_info['size_mb'] > 0:
                st.write(f"📊 Size: {db_info['size_mb']} MB")
        else:
            validation_errors = config.get_validation_errors()
            st.error(f"❌ Configuration issues found")
            for error in validation_errors:
                st.write(f"   - {error}")
            st.write("Please ensure your .env file is configured properly.")
        
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