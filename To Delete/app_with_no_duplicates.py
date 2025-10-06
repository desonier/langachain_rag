import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.retrievers.multi_query import MultiQueryRetriever

# Load environment variables from .env file
load_dotenv()

class ResumeRAGSystem:
    """Resume RAG System with update/no-duplicate functionality"""
    
    def __init__(self, persist_directory="./resume_vectordb"):
        self.persist_directory = persist_directory
        
        # Create embeddings
        self.embedding = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            model=os.getenv("EMBEDDING_MODEL")
        )
        
        # Track processed resumes to prevent duplicates
        self.processed_resumes = set()
        
        # Initialize system
        self._init_system()
    
    def _init_system(self):
        """Initialize vector database and LLM"""
        try:
            # Initialize database
            if os.path.exists(self.persist_directory):
                self.db = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embedding
                )
                print("📂 Loaded existing resume database")
                self._load_existing_resume_ids()
            else:
                self.db = Chroma(
                    embedding_function=self.embedding,
                    persist_directory=self.persist_directory
                )
                print("🆕 Created new resume database")
            
            # Initialize LLM
            self.llm = AzureChatOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                deployment_name=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
            )
            
            # Create RAG chain
            self._create_rag_chain()
            
        except Exception as e:
            print(f"❌ Error initializing system: {e}")
            raise
    
    def _load_existing_resume_ids(self):
        """Load existing resume IDs to prevent duplicates"""
        try:
            all_docs = self.db.similarity_search("", k=1000)
            for doc in all_docs:
                resume_id = doc.metadata.get('Resume_ID')
                if resume_id:
                    self.processed_resumes.add(resume_id)
            print(f"📋 Found {len(self.processed_resumes)} existing resumes in database")
        except Exception as e:
            print(f"⚠️ Could not load existing resume IDs: {e}")
    
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
    
    def _create_resume_metadata(self, file_path):
        """Create metadata for resume"""
        file_name = os.path.basename(file_path)
        file_extension = file_path.split('.')[-1].upper()
        resume_id = self._generate_resume_id(file_path)
        
        metadata = {
            "Resume_ID": resume_id,
            "Resume_Date": datetime.now().isoformat(),
            "Source": f"{file_extension} resume",
            "file_path": file_path,
            "content_type": "resume",
            "file_format": file_extension,
            "document_name": file_name,
            "last_updated": datetime.now().isoformat()
        }
        return metadata, resume_id
    
    def add_resume(self, file_path, force_update=False):
        """Add resume to database (prevents duplicates unless force_update=True)"""
        try:
            print(f"\n📄 Processing: {file_path}")
            
            # Generate metadata and Resume_ID
            file_metadata, resume_id = self._create_resume_metadata(file_path)
            
            # Check if already processed
            if resume_id in self.processed_resumes and not force_update:
                print(f"⏭️ Resume {resume_id} already exists. Skipping to prevent duplicates.")
                print("   💡 Use force_update=True to add updated version")
                return True, resume_id, 0
            
            if resume_id in self.processed_resumes and force_update:
                print(f"🔄 Adding updated version of resume: {resume_id}")
            else:
                print(f"🆕 Adding new resume: {resume_id}")
            
            # Load and process document
            documents = self._load_document(file_path)
            
            # Split into chunks
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            docs = text_splitter.split_documents(documents)
            
            # Add metadata to each chunk
            for i, doc in enumerate(docs):
                doc.metadata.update(file_metadata)
                doc.metadata["chunk_id"] = i
                doc.metadata["chunk_content"] = doc.page_content[:100]
                doc.metadata["total_chunks"] = len(docs)
                if force_update:
                    doc.metadata["update_timestamp"] = datetime.now().isoformat()
            
            # Add to database
            self.db.add_documents(docs)
            
            # Track as processed
            self.processed_resumes.add(resume_id)
            
            print(f"   ✅ Successfully processed {len(docs)} chunks")
            return True, resume_id, len(docs)
            
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")
            return False, None, 0
    
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

# Initialize the RAG system
print("🚀 Initializing Resume RAG System...")
rag_system = ResumeRAGSystem()

# Add resume files (will skip if already exists to prevent duplicates)
file_paths = [
    "./data/Brandon_Tobalski_1-28-2022.pdf",
    "./data/Brandon_Tobalski_1-28-2022.docx"
]

print("\n🔄 Adding resumes to database...")
for file_path in file_paths:
    rag_system.add_resume(file_path)

# List resumes in database
print("\n📋 Resumes in database:")
resumes = rag_system.list_resumes()
for resume in resumes:
    print(f"   - {resume['document_name']}: {resume['chunk_count']} chunks")

# Example queries
print("\n" + "="*60)
print("🔍 Example Queries:")

# Query 1: General question
query1 = "What is this resume about?"
print(f"\nQ1: {query1}")
response1 = rag_system.query(query1)
print(f"A1: {response1['result']}")

# Query 2: Specific information
query2 = "What certifications does Brandon have?"
print(f"\nQ2: {query2}")
response2 = rag_system.query(query2)
print(f"A2: {response2['result']}")

# Query 3: Metadata-based search
print(f"\nQ3: Search only DOCX resume for technical skills")
response3 = rag_system.search_by_metadata(
    "What are Brandon's technical skills?", 
    {"file_format": "DOCX"}
)
print(f"A3: {response3['result']}")

# Show source documents
print("\n=== Source Documents Example ===")
if 'source_documents' in response2 and response2['source_documents']:
    for i, doc in enumerate(response2['source_documents'][:2]):
        source_file = doc.metadata.get('document_name', 'Unknown')
        print(f"Document {i+1} from {source_file}:")
        print(f"   Content: {doc.page_content[:150]}...")
        print("   ---")

print(f"\n✅ Resume RAG System Ready!")
print(f"   - ✅ No duplicates: Automatically prevents duplicate resumes")
print(f"   - ✅ Multi-format: Supports PDF and DOCX files")
print(f"   - ✅ Smart search: Vector + semantic search capabilities")
print(f"   - ✅ Targeted queries: Can search specific resumes or all resumes")
print(f"   - ✅ Metadata filtering: Search by file format, content type, etc.")

# Instructions for usage
print(f"\n💡 Usage Examples:")
print(f"   # Add new resume:")
print(f"   rag_system.add_resume('./path/to/new_resume.pdf')")
print(f"   ")
print(f"   # Query all resumes:")
print(f"   response = rag_system.query('What experience does this person have?')")
print(f"   ")
print(f"   # Query specific resume:")
print(f"   response = rag_system.query('What skills?', resume_id='specific_id')")
print(f"   ")
print(f"   # Search with metadata filter:")
print(f"   response = rag_system.search_by_metadata('query', {{'file_format': 'PDF'}})")