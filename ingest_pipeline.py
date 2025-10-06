import os
import hashlib
import argparse
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_chroma import Chroma
import json
import re

# Load environment variables from .env file
load_dotenv()

class ResumeIngestPipeline:
    """Resume Ingestion Pipeline - Adds resumes to vector database with no-duplicate functionality"""
    
    def __init__(self, persist_directory="./resume_vectordb", enable_llm_parsing=True):
        self.persist_directory = persist_directory
        self.enable_llm_parsing = enable_llm_parsing
        
        # Create embeddings
        self.embedding = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            model=os.getenv("EMBEDDING_MODEL")
        )
        
        # Initialize LLM for parsing assistance if enabled
        if self.enable_llm_parsing:
            try:
                self.llm = AzureChatOpenAI(
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    api_key=os.getenv("AZURE_OPENAI_KEY"),
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                    deployment_name=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT"),
                    temperature=0.1,  # Low temperature for consistent parsing
                    model_kwargs={
                        "extra_headers": {
                            "ms-azure-ai-chat-enhancements-disable-search": "true"
                        }
                    }
                )
                print("🤖 LLM-assisted parsing enabled")
            except Exception as e:
                print(f"⚠️ Could not initialize LLM, falling back to basic parsing: {e}")
                self.enable_llm_parsing = False
        
        # Track processed resumes to prevent duplicates
        self.processed_resumes = set()
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize vector database"""
        try:
            if os.path.exists(self.persist_directory):
                self.db = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embedding
                )
                print("Loaded existing resume database")
                self._load_existing_resume_ids()
            else:
                self.db = Chroma(
                    embedding_function=self.embedding,
                    persist_directory=self.persist_directory
                )
                print("Created new resume database")
                
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def _load_existing_resume_ids(self):
        """Load existing resume IDs to prevent duplicates"""
        try:
            all_docs = self.db.similarity_search("", k=1000)
            for doc in all_docs:
                resume_id = doc.metadata.get('Resume_ID')
                if resume_id:
                    self.processed_resumes.add(resume_id)
            print(f"Found {len(self.processed_resumes)} existing resumes in database")
        except Exception as e:
            print(f"Could not load existing resume IDs: {e}")
    
    def _generate_resume_id(self, file_path):
        """Generate consistent Resume_ID based on file path"""
        file_name = os.path.basename(file_path)
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"{file_name}_{file_hash}"
    
    def _load_document(self, file_path):
        """Load document based on file extension"""
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            return loader.load()
        elif file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
            return loader.load()
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
    
    def _extract_resume_structure(self, content):
        """Use LLM to extract structured information from resume content"""
        if not self.enable_llm_parsing:
            return {}
        
        try:
            extraction_prompt = """
            Analyze the following resume content and extract key information in JSON format.
            
            Extract the following fields:
            - candidate_name: Full name of the candidate
            - contact_info: Email, phone, location (as a single string)
            - key_skills: List of main technical and professional skills (max 10)
            - experience_years: Estimated total years of experience (as number)
            - education: Highest degree and field (as single string)
            - certifications: List of certifications mentioned (max 5)
            - job_titles: List of most recent job titles (max 3)
            - industries: List of industries/domains mentioned (max 3)
            
            Return ONLY valid JSON without any explanation.
            
            Resume Content:
            {content}
            """
            
            response = self.llm.invoke(extraction_prompt.format(content=content[:4000]))  # Limit content length
            
            # Parse the JSON response
            try:
                extracted_data = json.loads(response.content)
                return extracted_data
            except json.JSONDecodeError:
                # Try to extract JSON from the response if it's wrapped in other text
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                    return extracted_data
                else:
                    print("⚠️ Could not parse LLM response as JSON")
                    return {}
                    
        except Exception as e:
            print(f"⚠️ Error in LLM content extraction: {e}")
            return {}
    
    def _identify_resume_sections(self, content):
        """Use LLM to identify logical sections in the resume for better chunking"""
        if not self.enable_llm_parsing:
            return []
        
        try:
            section_prompt = """
            Analyze the following resume content and identify the main sections.
            
            Return a JSON list of sections with their approximate start positions (character index).
            Each section should have: "section_name", "start_position", "content_preview"
            
            Common sections include: Contact Information, Summary/Objective, Experience, Education, Skills, Certifications, Projects, etc.
            
            Return ONLY valid JSON without any explanation.
            
            Resume Content:
            {content}
            """
            
            response = self.llm.invoke(section_prompt.format(content=content[:3000]))
            
            try:
                sections = json.loads(response.content)
                return sections if isinstance(sections, list) else []
            except json.JSONDecodeError:
                json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
                if json_match:
                    sections = json.loads(json_match.group())
                    return sections if isinstance(sections, list) else []
                else:
                    return []
                    
        except Exception as e:
            print(f"⚠️ Error in section identification: {e}")
            return []
    
    def _create_semantic_chunks(self, documents, extracted_info=None):
        """Create semantically meaningful chunks using LLM-identified sections"""
        if not self.enable_llm_parsing or not documents:
            # Fallback to traditional chunking
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            return text_splitter.split_documents(documents)
        
        try:
            # Get the full text content
            full_content = "\n".join([doc.page_content for doc in documents])
            
            # Identify sections using LLM
            sections = self._identify_resume_sections(full_content)
            
            if not sections:
                # Fallback to traditional chunking if section identification fails
                text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                return text_splitter.split_documents(documents)
            
            # Create chunks based on identified sections
            semantic_chunks = []
            
            for i, section in enumerate(sections):
                section_name = section.get('section_name', f'Section_{i}')
                start_pos = section.get('start_position', 0)
                
                # Determine end position (start of next section or end of content)
                if i + 1 < len(sections):
                    end_pos = sections[i + 1].get('start_position', len(full_content))
                else:
                    end_pos = len(full_content)
                
                # Extract section content
                section_content = full_content[start_pos:end_pos].strip()
                
                if section_content and len(section_content) > 50:  # Only include substantial sections
                    # Create document chunk
                    from langchain.schema import Document
                    chunk = Document(
                        page_content=section_content,
                        metadata={
                            'section_name': section_name,
                            'section_order': i,
                            'chunk_type': 'semantic_section'
                        }
                    )
                    semantic_chunks.append(chunk)
            
            # If no semantic chunks were created, fallback to traditional chunking
            if not semantic_chunks:
                text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                return text_splitter.split_documents(documents)
            
            print(f"   📝 Created {len(semantic_chunks)} semantic chunks")
            return semantic_chunks
            
        except Exception as e:
            print(f"⚠️ Error in semantic chunking, using traditional chunking: {e}")
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            return text_splitter.split_documents(documents)
    
    def _create_resume_metadata(self, file_path, extracted_info=None, original_filename=None):
        """Create metadata for resume with LLM-extracted information"""
        # Use original filename if provided, otherwise use file path
        display_path = original_filename or file_path
        file_name = os.path.basename(display_path)
        file_extension = display_path.split('.')[-1].upper()
        
        # Generate Resume_ID based on original filename if available
        id_source = original_filename or file_path
        resume_id = self._generate_resume_id(id_source)
        
        # Base metadata
        metadata = {
            "Resume_ID": resume_id,
            "Resume_Date": datetime.now().isoformat(),
            "Source": f"{file_extension} resume",
            "file_path": file_path,  # Keep actual file path for processing
            "original_file_source": os.path.abspath(original_filename) if original_filename else os.path.abspath(file_path),
            "display_filename": file_name,  # Add display filename for UI
            "content_type": "resume",
            "file_format": file_extension,
            "document_name": file_name,
            "last_updated": datetime.now().isoformat(),
            "parsing_method": "llm_assisted" if self.enable_llm_parsing else "basic"
        }
        
        # Add LLM-extracted information if available
        if extracted_info and isinstance(extracted_info, dict):
            # Add candidate information
            if extracted_info.get('candidate_name'):
                metadata['candidate_name'] = extracted_info['candidate_name']
            
            if extracted_info.get('contact_info'):
                metadata['contact_info'] = extracted_info['contact_info']
            
            # Add skills as a searchable field
            if extracted_info.get('key_skills'):
                skills = extracted_info['key_skills']
                if isinstance(skills, list):
                    metadata['key_skills'] = ', '.join(skills)
                    metadata['skills_count'] = len(skills)
                else:
                    metadata['key_skills'] = str(skills)
            
            # Add experience information
            if extracted_info.get('experience_years'):
                try:
                    metadata['experience_years'] = int(extracted_info['experience_years'])
                except (ValueError, TypeError):
                    metadata['experience_years'] = 0
            
            # Add education
            if extracted_info.get('education'):
                metadata['education'] = extracted_info['education']
            
            # Add certifications
            if extracted_info.get('certifications'):
                certs = extracted_info['certifications']
                if isinstance(certs, list) and certs:
                    metadata['certifications'] = ', '.join(certs)
                    metadata['certifications_count'] = len(certs)
                elif certs:
                    metadata['certifications'] = str(certs)
            
            # Add job titles
            if extracted_info.get('job_titles'):
                titles = extracted_info['job_titles']
                if isinstance(titles, list) and titles:
                    metadata['recent_job_titles'] = ', '.join(titles)
                elif titles:
                    metadata['recent_job_titles'] = str(titles)
            
            # Add industries
            if extracted_info.get('industries'):
                industries = extracted_info['industries']
                if isinstance(industries, list) and industries:
                    metadata['industries'] = ', '.join(industries)
                elif industries:
                    metadata['industries'] = str(industries)
        
        return metadata, resume_id
    
    def add_resume(self, file_path, force_update=False, original_filename=None):
        """Add resume to database (prevents duplicates unless force_update=True)"""
        try:
            print(f"\n Processing: {original_filename or file_path}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False, None, 0
            
            # Generate metadata and Resume_ID using original filename if provided
            display_name = original_filename or file_path
            file_metadata, resume_id = self._create_resume_metadata(file_path, original_filename=original_filename)
            
            # Check if already processed
            if resume_id in self.processed_resumes and not force_update:
                print(f"⏭ Resume {resume_id} already exists. Skipping to prevent duplicates.")
                print("Use --force-update to add updated version")
                return True, resume_id, 0
            
            if resume_id in self.processed_resumes and force_update:
                print(f" Adding updated version of resume: {resume_id}")
            else:
                print(f" Adding new resume: {resume_id}")
            
            # Load and process document
            documents = self._load_document(file_path)
            
            # Extract structured information using LLM
            extracted_info = {}
            if self.enable_llm_parsing and documents:
                full_content = "\n".join([doc.page_content for doc in documents])
                print("   🤖 Analyzing resume content with LLM...")
                extracted_info = self._extract_resume_structure(full_content)
                
                if extracted_info:
                    candidate_name = extracted_info.get('candidate_name', 'Unknown')
                    skills_count = len(extracted_info.get('key_skills', []))
                    exp_years = extracted_info.get('experience_years', 0)
                    print(f"   📊 Extracted: {candidate_name}, {skills_count} skills, {exp_years} years experience")
            
            # Generate metadata with extracted information
            file_metadata, resume_id = self._create_resume_metadata(file_path, extracted_info)
            
            # Create semantic chunks using LLM-identified sections
            print("   📝 Creating semantic chunks...")
            docs = self._create_semantic_chunks(documents, extracted_info)
            
            # Add metadata to each chunk
            for i, doc in enumerate(docs):
                # Add base metadata
                doc.metadata.update(file_metadata)
                doc.metadata["chunk_id"] = i
                doc.metadata["chunk_content"] = doc.page_content[:100]
                doc.metadata["total_chunks"] = len(docs)
                
                # Add section-specific metadata if available
                if hasattr(doc, 'metadata') and doc.metadata.get('section_name'):
                    doc.metadata["section_name"] = doc.metadata.get('section_name')
                    doc.metadata["section_order"] = doc.metadata.get('section_order', i)
                    doc.metadata["chunk_type"] = doc.metadata.get('chunk_type', 'semantic_section')
                else:
                    doc.metadata["chunk_type"] = "traditional"
                
                if force_update:
                    doc.metadata["update_timestamp"] = datetime.now().isoformat()
            
            # Add to database
            self.db.add_documents(docs)
            
            # Track as processed
            self.processed_resumes.add(resume_id)
            
            print(f"Successfully processed {len(docs)} chunks")
            return True, resume_id, len(docs)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, None, 0
    
    def add_directory(self, directory_path, force_update=False):
        """Add all resumes from a directory"""
        if not os.path.exists(directory_path):
            print(f" Directory not found: {directory_path}")
            return
        
        supported_extensions = ['.pdf', '.docx']
        files_processed = 0
        chunks_added = 0
        
        print(f"Scanning directory: {directory_path}")
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in supported_extensions):
                    file_path = os.path.join(root, file)
                    success, resume_id, chunk_count = self.add_resume(file_path, force_update)
                    if success:
                        files_processed += 1
                        chunks_added += chunk_count
        
        print(f"\n Directory processing complete:")
        print(f"   - Files processed: {files_processed}")
        print(f"   - Total chunks added: {chunks_added}")
    
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
                        'original_file_source': doc.metadata.get('original_file_source', doc.metadata.get('file_path')),
                        'last_updated': doc.metadata.get('last_updated'),
                        'chunk_count': 0
                    }
                resume_info[resume_id]['chunk_count'] += 1
            
            return list(resume_info.values())
            
        except Exception as e:
            print(f" Error listing resumes: {e}")
            return []
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            resumes = self.list_resumes()
            total_chunks = sum(resume['chunk_count'] for resume in resumes)
            
            stats = {
                'total_resumes': len(resumes),
                'total_chunks': total_chunks,
                'file_formats': {},
                'database_path': self.persist_directory
            }
            
            for resume in resumes:
                file_format = resume['file_format']
                if file_format not in stats['file_formats']:
                    stats['file_formats'][file_format] = 0
                stats['file_formats'][file_format] += 1
            
            return stats
            
        except Exception as e:
            print(f" Error getting database stats: {e}")
            return {}

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Resume Ingestion Pipeline - Add resumes to vector database')
    parser.add_argument('--file', '-f', help='Path to resume file to add')
    parser.add_argument('--directory', '-d', help='Directory containing resume files to add')
    parser.add_argument('--list', '-l', action='store_true', help='List all resumes in database')
    parser.add_argument('--stats', '-s', action='store_true', help='Show database statistics')
    parser.add_argument('--force-update', action='store_true', help='Force update existing resumes')
    parser.add_argument('--db-path', default='./resume_vectordb', help='Path to vector database (default: ./resume_vectordb)')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM-assisted parsing (faster but less structured)')
    
    args = parser.parse_args()
    
    print(" Resume Ingestion Pipeline")
    if not args.no_llm:
        print("🤖 LLM-Assisted Parsing Enabled")
    print("=" * 40)
    
    # Initialize pipeline
    pipeline = ResumeIngestPipeline(
        persist_directory=args.db_path,
        enable_llm_parsing=not args.no_llm
    )
    
    # Handle different operations
    if args.file:
        print(f"\n Adding single file...")
        success, resume_id, chunks = pipeline.add_resume(args.file, args.force_update)
        if success and chunks > 0:
            print(f" Added {chunks} chunks for resume {resume_id}")
        elif success and chunks == 0:
            print(f"Resume {resume_id} already exists (use --force-update to update)")
    
    elif args.directory:
        print(f"\n Adding directory...")
        pipeline.add_directory(args.directory, args.force_update)
    
    elif args.list:
        print(f"\n Resumes in database:")
        resumes = pipeline.list_resumes()
        if resumes:
            for resume in resumes:
                print(f"   - {resume['document_name']} ({resume['file_format']}): {resume['chunk_count']} chunks")
        else:
            print("   No resumes found in database")
    
    elif args.stats:
        print(f"\n Database Statistics:")
        stats = pipeline.get_database_stats()
        if stats:
            print(f"   - Total resumes: {stats['total_resumes']}")
            print(f"   - Total chunks: {stats['total_chunks']}")
            print(f"   - Database path: {stats['database_path']}")
            print("   - File formats:")
            for format_type, count in stats['file_formats'].items():
                print(f"     • {format_type}: {count} files")
        else:
            print("   Could not retrieve statistics")
    
    else:
        print("\n Usage examples:")
        print("   python ingest_pipeline.py --file ./data/resume.pdf")
        print("   python ingest_pipeline.py --directory ./data")
        print("   python ingest_pipeline.py --list")
        print("   python ingest_pipeline.py --stats")
        print("   python ingest_pipeline.py --file ./data/resume.pdf --force-update")

if __name__ == "__main__":
    main()