import os
import uuid
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import Document

# Load environment variables from .env file
load_dotenv()

class ResumeVectorDB:
    def __init__(self, persist_directory="./chroma_store"):
        self.persist_directory = persist_directory
        self.embedding = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            model=os.getenv("EMBEDDING_MODEL")
        )
        
        # Initialize or load existing database
        self._init_database()
    
    def _init_database(self):
        """Initialize database or load existing one"""
        try:
            # Try to load existing database
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding
            )
            print("📂 Loaded existing ChromaDB")
        except:
            # Create new database if none exists
            self.db = Chroma(
                embedding_function=self.embedding,
                persist_directory=self.persist_directory
            )
            print("🆕 Created new ChromaDB")
    
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
    
    def _resume_exists(self, resume_id):
        """Check if resume with given ID already exists"""
        try:
            # Search for existing documents with this Resume_ID
            existing_docs = self.db.similarity_search(
                "", 
                k=100,  # Get enough to check all documents
                filter={"Resume_ID": resume_id}
            )
            return len(existing_docs) > 0, existing_docs
        except:
            return False, []
    
    def _remove_existing_resume(self, resume_id):
        """Remove existing resume chunks from database"""
        try:
            # Get all documents
            all_docs = self.db.similarity_search("", k=1000)
            
            # Find documents with matching Resume_ID
            docs_to_remove = []
            remaining_docs = []
            
            for doc in all_docs:
                if doc.metadata.get('Resume_ID') == resume_id:
                    docs_to_remove.append(doc)
                else:
                    remaining_docs.append(doc)
            
            if docs_to_remove:
                print(f"🗑️ Removing {len(docs_to_remove)} existing chunks for Resume_ID: {resume_id}")
                
                # Recreate database without the old documents
                if remaining_docs:
                    # Clear and rebuild with remaining documents
                    self._clear_database()
                    self.db = Chroma.from_documents(
                        documents=remaining_docs,
                        embedding=self.embedding,
                        persist_directory=self.persist_directory
                    )
                else:
                    # If no remaining documents, clear completely
                    self._clear_database()
                    self.db = Chroma(
                        embedding_function=self.embedding,
                        persist_directory=self.persist_directory
                    )
                
                return True
            return False
            
        except Exception as e:
            print(f"⚠️ Error removing existing resume: {e}")
            return False
    
    def _clear_database(self):
        """Clear the entire database"""
        import shutil
        if os.path.exists(self.persist_directory):
            try:
                shutil.rmtree(self.persist_directory)
                print("🗑️ Cleared ChromaDB directory")
            except Exception as e:
                print(f"⚠️ Could not clear database: {e}")
    
    def add_or_update_resume(self, file_path):
        """Add new resume or update existing one"""
        try:
            print(f"\n📄 Processing: {file_path}")
            
            # Generate metadata and Resume_ID
            file_metadata, resume_id = self._create_resume_metadata(file_path)
            
            # Check if resume already exists
            exists, existing_docs = self._resume_exists(resume_id)
            
            if exists:
                print(f"🔄 Resume with ID {resume_id} already exists. Updating...")
                # Remove existing version
                self._remove_existing_resume(resume_id)
            else:
                print(f"🆕 Adding new resume with ID: {resume_id}")
            
            # Load and process document
            documents = self._load_document(file_path)
            full_text = " ".join([doc.page_content for doc in documents])
            
            # Split into chunks
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            docs = text_splitter.split_documents(documents)
            
            # Add metadata to each chunk
            for i, doc in enumerate(docs):
                doc.metadata.update(file_metadata)
                doc.metadata["chunk_id"] = i
                doc.metadata["chunk_content"] = doc.page_content[:100]
                doc.metadata["total_chunks"] = len(docs)
            
            # Add to database
            if hasattr(self.db, '_collection') and self.db._collection.count() > 0:
                # Add to existing database
                self.db.add_documents(docs)
            else:
                # Create new database
                self.db = Chroma.from_documents(
                    documents=docs,
                    embedding=self.embedding,
                    persist_directory=self.persist_directory
                )
            
            print(f"   ✅ Successfully processed {len(docs)} chunks")
            return True, resume_id, len(docs)
            
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")
            return False, None, 0
    
    def add_multiple_resumes(self, file_paths):
        """Add or update multiple resumes"""
        print("🔄 Processing multiple resumes with update capability...")
        
        results = []
        total_chunks = 0
        
        for file_path in file_paths:
            success, resume_id, chunk_count = self.add_or_update_resume(file_path)
            results.append({
                'file_path': file_path,
                'success': success,
                'resume_id': resume_id,
                'chunks': chunk_count
            })
            if success:
                total_chunks += chunk_count
        
        print(f"\n📊 Processing Summary:")
        print(f"   Total files processed: {len(file_paths)}")
        print(f"   Successful: {sum(1 for r in results if r['success'])}")
        print(f"   Total chunks: {total_chunks}")
        
        return results
    
    def list_all_resumes(self):
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
                        'last_updated': doc.metadata.get('last_updated'),
                        'chunk_count': 0
                    }
                resume_info[resume_id]['chunk_count'] += 1
            
            return list(resume_info.values())
            
        except Exception as e:
            print(f"❌ Error listing resumes: {e}")
            return []
    
    def search_resume(self, query, resume_id=None, k=5):
        """Search specific resume or all resumes"""
        try:
            if resume_id:
                # Search specific resume
                results = self.db.similarity_search(
                    query, 
                    k=k, 
                    filter={"Resume_ID": resume_id}
                )
                print(f"🔍 Searching resume {resume_id} for: '{query}'")
            else:
                # Search all resumes
                results = self.db.similarity_search(query, k=k)
                print(f"🔍 Searching all resumes for: '{query}'")
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []

def test_update_functionality():
    """Test the update functionality"""
    print("=== Testing Resume Update Functionality ===\n")
    
    # Initialize database
    resume_db = ResumeVectorDB()
    
    # Test files
    file_paths = [
        "./data/Brandon_Tobalski_1-28-2022.pdf",
        "./data/Brandon_Tobalski_1-28-2022.docx"
    ]
    
    # First addition
    print("🟢 FIRST ADDITION:")
    results1 = resume_db.add_multiple_resumes(file_paths)
    
    # List resumes
    print("\n📋 Resumes after first addition:")
    resumes = resume_db.list_all_resumes()
    for resume in resumes:
        print(f"   - {resume['document_name']} (ID: {resume['resume_id']}) - {resume['chunk_count']} chunks")
    
    # Simulate update (add same files again)
    print("\n🟡 SECOND ADDITION (Should Update):")
    results2 = resume_db.add_multiple_resumes(file_paths)
    
    # List resumes again
    print("\n📋 Resumes after second addition:")
    resumes = resume_db.list_all_resumes()
    for resume in resumes:
        print(f"   - {resume['document_name']} (ID: {resume['resume_id']}) - {resume['chunk_count']} chunks")
    
    # Test search
    print("\n🔍 Testing search functionality:")
    results = resume_db.search_resume("cybersecurity certifications", k=3)
    print(f"Found {len(results)} results")
    
    return resume_db

if __name__ == "__main__":
    # Test the update functionality
    resume_db = test_update_functionality()