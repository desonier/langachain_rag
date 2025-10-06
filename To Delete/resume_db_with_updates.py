import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
import chromadb

# Load environment variables
load_dotenv()

class SmartResumeVectorDB:
    def __init__(self, persist_directory="./chroma_store_smart"):
        self.persist_directory = persist_directory
        self.collection_name = "resumes"
        
        # Create embeddings
        self.embedding = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            model=os.getenv("EMBEDDING_MODEL")
        )
        
        # Initialize ChromaDB client and collection
        self._init_database()
    
    def _init_database(self):
        """Initialize ChromaDB with proper collection management"""
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                print(f"📂 Loaded existing collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(name=self.collection_name)
                print(f"🆕 Created new collection: {self.collection_name}")
            
            # Create LangChain wrapper
            self.db = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embedding
            )
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            raise
    
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
    
    def _get_existing_chunk_ids(self, resume_id):
        """Get all chunk IDs for a specific resume"""
        try:
            # Query ChromaDB directly for this resume
            results = self.collection.get(
                where={"Resume_ID": resume_id},
                include=['ids']
            )
            return results['ids'] if results['ids'] else []
        except Exception as e:
            print(f"⚠️ Error getting existing chunks: {e}")
            return []
    
    def _delete_existing_resume(self, resume_id):
        """Delete all chunks for a specific resume"""
        try:
            existing_ids = self._get_existing_chunk_ids(resume_id)
            
            if existing_ids:
                print(f"🗑️ Deleting {len(existing_ids)} existing chunks for Resume_ID: {resume_id}")
                self.collection.delete(ids=existing_ids)
                return len(existing_ids)
            return 0
            
        except Exception as e:
            print(f"⚠️ Error deleting existing resume: {e}")
            return 0
    
    def add_or_update_resume(self, file_path):
        """Add new resume or update existing one"""
        try:
            print(f"\n📄 Processing: {file_path}")
            
            # Generate metadata and Resume_ID
            file_metadata, resume_id = self._create_resume_metadata(file_path)
            
            # Check for existing resume and delete if found
            deleted_count = self._delete_existing_resume(resume_id)
            
            if deleted_count > 0:
                print(f"🔄 Updated existing resume (removed {deleted_count} old chunks)")
            else:
                print(f"🆕 Adding new resume with ID: {resume_id}")
            
            # Load and process document
            documents = self._load_document(file_path)
            
            # Split into chunks
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            docs = text_splitter.split_documents(documents)
            
            # Create unique IDs for each chunk
            chunk_ids = []
            chunk_texts = []
            chunk_metadatas = []
            
            for i, doc in enumerate(docs):
                # Create unique chunk ID
                chunk_id = f"{resume_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(doc.page_content)
                
                # Add metadata
                chunk_metadata = file_metadata.copy()
                chunk_metadata["chunk_id"] = i
                chunk_metadata["chunk_content"] = doc.page_content[:100]
                chunk_metadata["total_chunks"] = len(docs)
                chunk_metadata["unique_chunk_id"] = chunk_id
                chunk_metadatas.append(chunk_metadata)
            
            # Add to ChromaDB using direct API
            self.collection.add(
                ids=chunk_ids,
                documents=chunk_texts,
                metadatas=chunk_metadatas
            )
            
            print(f"   ✅ Successfully added {len(docs)} chunks")
            return True, resume_id, len(docs)
            
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")
            return False, None, 0
    
    def list_all_resumes(self):
        """List all resumes in database"""
        try:
            # Get all documents
            all_data = self.collection.get(include=['metadatas'])
            
            if not all_data['metadatas']:
                return []
            
            resume_info = {}
            for metadata in all_data['metadatas']:
                resume_id = metadata.get('Resume_ID')
                if resume_id and resume_id not in resume_info:
                    resume_info[resume_id] = {
                        'resume_id': resume_id,
                        'document_name': metadata.get('document_name'),
                        'file_format': metadata.get('file_format'),
                        'file_path': metadata.get('file_path'),
                        'last_updated': metadata.get('last_updated'),
                        'chunk_count': 0
                    }
                if resume_id:
                    resume_info[resume_id]['chunk_count'] += 1
            
            return list(resume_info.values())
            
        except Exception as e:
            print(f"❌ Error listing resumes: {e}")
            return []
    
    def search_resume(self, query, resume_id=None, k=5):
        """Search specific resume or all resumes"""
        try:
            if resume_id:
                # Search specific resume using LangChain wrapper
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
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            count = self.collection.count()
            resumes = self.list_all_resumes()
            
            return {
                'total_chunks': count,
                'total_resumes': len(resumes),
                'resumes': resumes
            }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {'total_chunks': 0, 'total_resumes': 0, 'resumes': []}

def test_smart_update():
    """Test the smart update functionality"""
    print("=== Testing Smart Resume Update Functionality ===\n")
    
    # Initialize smart database
    smart_db = SmartResumeVectorDB()
    
    # Test files
    file_paths = [
        "./data/Brandon_Tobalski_1-28-2022.pdf",
        "./data/Brandon_Tobalski_1-28-2022.docx"
    ]
    
    # First addition
    print("🟢 FIRST ADDITION:")
    for file_path in file_paths:
        success, resume_id, chunks = smart_db.add_or_update_resume(file_path)
    
    print("\n📊 Database stats after first addition:")
    stats1 = smart_db.get_database_stats()
    print(f"   Total chunks: {stats1['total_chunks']}")
    print(f"   Total resumes: {stats1['total_resumes']}")
    for resume in stats1['resumes']:
        print(f"   - {resume['document_name']}: {resume['chunk_count']} chunks")
    
    # Second addition (should update, not duplicate)
    print("\n🟡 SECOND ADDITION (Should Update, Not Duplicate):")
    for file_path in file_paths:
        success, resume_id, chunks = smart_db.add_or_update_resume(file_path)
    
    print("\n📊 Database stats after second addition:")
    stats2 = smart_db.get_database_stats()
    print(f"   Total chunks: {stats2['total_chunks']}")
    print(f"   Total resumes: {stats2['total_resumes']}")
    for resume in stats2['resumes']:
        print(f"   - {resume['document_name']}: {resume['chunk_count']} chunks")
    
    # Verify no duplication
    print(f"\n✅ VERIFICATION:")
    if stats1['total_chunks'] == stats2['total_chunks']:
        print("✅ SUCCESS: No duplicates created! Chunks were properly updated.")
    else:
        print(f"❌ ISSUE: Chunk count changed from {stats1['total_chunks']} to {stats2['total_chunks']}")
    
    # Test search
    print("\n🔍 Testing search:")
    results = smart_db.search_resume("cybersecurity certifications", k=3)
    print(f"Found {len(results)} results")
    
    return smart_db

if __name__ == "__main__":
    # Test the smart update functionality
    smart_db = test_smart_update()