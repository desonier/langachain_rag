import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA

# Load environment variables
load_dotenv()

class ResumeVectorDBManager:
    """Smart Resume Vector Database with update/no-duplicate functionality"""
    
    def __init__(self, persist_directory="./chroma_store_final"):
        self.persist_directory = persist_directory
        
        # Create embeddings
        self.embedding = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            model=os.getenv("EMBEDDING_MODEL")
        )
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize or load existing ChromaDB"""
        try:
            # Try to load existing database
            if os.path.exists(self.persist_directory):
                self.db = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embedding
                )
                print("📂 Loaded existing ChromaDB")
            else:
                # Create new database
                self.db = Chroma(
                    embedding_function=self.embedding,
                    persist_directory=self.persist_directory
                )
                print("🆕 Created new ChromaDB")
                
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            # Force create new database
            self._clear_database()
            self.db = Chroma(
                embedding_function=self.embedding,
                persist_directory=self.persist_directory
            )
            print("🆕 Created fresh ChromaDB after error")
    
    def _clear_database(self):
        """Clear the database directory"""
        import shutil
        if os.path.exists(self.persist_directory):
            try:
                shutil.rmtree(self.persist_directory)
                print("🗑️ Cleared existing database")
            except Exception as e:
                print(f"⚠️ Could not clear database: {e}")
    
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
        """Check if resume already exists and return existing documents"""
        try:
            # Search for existing documents with this Resume_ID
            existing_docs = self.db.similarity_search(
                "", 
                k=200,  # Get many to ensure we get all chunks
                filter={"Resume_ID": resume_id}
            )
            return len(existing_docs) > 0, existing_docs
        except:
            return False, []
    
    def _rebuild_database_without_resume(self, resume_id_to_exclude):
        """Rebuild database excluding specific resume"""
        try:
            # Get all documents
            all_docs = self.db.similarity_search("", k=1000)
            
            # Filter out documents with the specified Resume_ID
            remaining_docs = [
                doc for doc in all_docs 
                if doc.metadata.get('Resume_ID') != resume_id_to_exclude
            ]
            
            print(f"🔧 Rebuilding database: removing {len(all_docs) - len(remaining_docs)} chunks")
            
            # Clear and rebuild
            self._clear_database()
            
            if remaining_docs:
                self.db = Chroma.from_documents(
                    documents=remaining_docs,
                    embedding=self.embedding,
                    persist_directory=self.persist_directory
                )
            else:
                self.db = Chroma(
                    embedding_function=self.embedding,
                    persist_directory=self.persist_directory
                )
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error rebuilding database: {e}")
            return False
    
    def add_or_update_resume(self, file_path):
        """Add new resume or update existing one (removes duplicates)"""
        try:
            print(f"\n📄 Processing: {file_path}")
            
            # Generate metadata and Resume_ID
            file_metadata, resume_id = self._create_resume_metadata(file_path)
            
            # Check if resume already exists
            exists, existing_docs = self._resume_exists(resume_id)
            
            if exists:
                print(f"🔄 Resume {resume_id} exists ({len(existing_docs)} chunks). Updating...")
                # Remove existing version by rebuilding database
                self._rebuild_database_without_resume(resume_id)
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
            
            # Add to database
            self.db.add_documents(docs)
            
            print(f"   ✅ Successfully processed {len(docs)} chunks")
            return True, resume_id, len(docs)
            
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")
            return False, None, 0
    
    def add_multiple_resumes(self, file_paths):
        """Add or update multiple resumes"""
        print("🔄 Processing multiple resumes...")
        
        results = []
        for file_path in file_paths:
            success, resume_id, chunks = self.add_or_update_resume(file_path)
            results.append({
                'file_path': file_path,
                'success': success,
                'resume_id': resume_id,
                'chunks': chunks
            })
        
        # Summary
        successful = [r for r in results if r['success']]
        total_chunks = sum(r['chunks'] for r in successful)
        
        print(f"\n📊 Summary:")
        print(f"   Files processed: {len(file_paths)}")
        print(f"   Successful: {len(successful)}")
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
                        'file_path': doc.metadata.get('file_path'),
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
                results = self.db.similarity_search(
                    query, 
                    k=k, 
                    filter={"Resume_ID": resume_id}
                )
                print(f"🔍 Searching resume {resume_id}: '{query}'")
            else:
                results = self.db.similarity_search(query, k=k)
                print(f"🔍 Searching all resumes: '{query}'")
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []
    
    def get_rag_chain(self):
        """Get RAG chain for question answering"""
        try:
            llm = AzureChatOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                deployment_name=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
            )
            
            retriever = self.db.as_retriever(search_kwargs={"k": 4})
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm, 
                retriever=retriever,
                return_source_documents=True
            )
            
            return qa_chain
            
        except Exception as e:
            print(f"❌ Error creating RAG chain: {e}")
            return None

def demonstrate_update_functionality():
    """Demonstrate the update functionality"""
    print("=== Resume Vector DB with Update Functionality ===\n")
    
    # Initialize database manager
    resume_db = ResumeVectorDBManager()
    
    # Test files
    files = [
        "./data/Brandon_Tobalski_1-28-2022.pdf",
        "./data/Brandon_Tobalski_1-28-2022.docx"
    ]
    
    # First addition
    print("🟢 FIRST ADDITION:")
    results1 = resume_db.add_multiple_resumes(files)
    
    print("\n📋 Resumes in database:")
    resumes1 = resume_db.list_all_resumes()
    for resume in resumes1:
        print(f"   - {resume['document_name']}: {resume['chunk_count']} chunks")
    
    # Second addition (should update, not duplicate)
    print(f"\n🟡 SECOND ADDITION (Update Test):")
    results2 = resume_db.add_multiple_resumes(files)
    
    print("\n📋 Resumes after update:")
    resumes2 = resume_db.list_all_resumes()
    for resume in resumes2:
        print(f"   - {resume['document_name']}: {resume['chunk_count']} chunks")
    
    # Verify update worked
    total1 = sum(r['chunk_count'] for r in resumes1)
    total2 = sum(r['chunk_count'] for r in resumes2)
    
    print(f"\n✅ UPDATE VERIFICATION:")
    print(f"   Before: {total1} chunks")
    print(f"   After: {total2} chunks")
    
    if total1 == total2:
        print("   ✅ SUCCESS: No duplicates! Updates working correctly.")
    else:
        print("   ❌ ISSUE: Chunk count changed - may have duplicates")
    
    # Test search functionality
    print(f"\n🔍 SEARCH TEST:")
    results = resume_db.search_resume("cybersecurity experience", k=3)
    print(f"   Found {len(results)} results")
    
    for i, doc in enumerate(results[:2]):
        source = doc.metadata.get('document_name', 'Unknown')
        resume_id = doc.metadata.get('Resume_ID', 'Unknown')
        print(f"   {i+1}. Source: {source}")
        print(f"      Content: {doc.page_content[:100]}...")
    
    return resume_db

if __name__ == "__main__":
    # Demonstrate the functionality
    db_manager = demonstrate_update_functionality()