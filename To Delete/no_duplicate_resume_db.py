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

class UpdateableResumeDB:
    """Resume Vector DB that properly handles updates without duplicates"""
    
    def __init__(self, persist_directory="./resumes_vectordb"):
        self.persist_directory = persist_directory
        
        # Create embeddings
        self.embedding = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            model=os.getenv("EMBEDDING_MODEL")
        )
        
        # Track processed resumes to avoid duplicates
        self.processed_resumes = set()
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database"""
        try:
            if os.path.exists(self.persist_directory):
                self.db = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embedding
                )
                print("📂 Loaded existing database")
                # Load existing resume IDs
                self._load_existing_resume_ids()
            else:
                self.db = Chroma(
                    embedding_function=self.embedding,
                    persist_directory=self.persist_directory
                )
                print("🆕 Created new database")
        except Exception as e:
            print(f"Error initializing: {e}")
    
    def _load_existing_resume_ids(self):
        """Load existing resume IDs to track what's already in database"""
        try:
            all_docs = self.db.similarity_search("", k=1000)
            for doc in all_docs:
                resume_id = doc.metadata.get('Resume_ID')
                if resume_id:
                    self.processed_resumes.add(resume_id)
            print(f"📋 Found {len(self.processed_resumes)} existing resumes")
        except:
            print("⚠️ Could not load existing resume IDs")
    
    def _generate_resume_id(self, file_path):
        """Generate consistent Resume_ID"""
        file_name = os.path.basename(file_path)
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"{file_name}_{file_hash}"
    
    def _load_document(self, file_path):
        """Load document based on extension"""
        if file_path.endswith('.pdf'):
            return PyPDFLoader(file_path).load()
        elif file_path.endswith('.docx'):
            return Docx2txtLoader(file_path).load()
        else:
            raise ValueError(f"Unsupported format: {file_path}")
    
    def _create_metadata(self, file_path):
        """Create metadata for resume"""
        file_name = os.path.basename(file_path)
        file_ext = file_path.split('.')[-1].upper()
        resume_id = self._generate_resume_id(file_path)
        
        return {
            "Resume_ID": resume_id,
            "document_name": file_name,
            "file_format": file_ext,
            "file_path": file_path,
            "content_type": "resume",
            "Source": f"{file_ext} resume",
            "processed_date": datetime.now().isoformat()
        }, resume_id
    
    def add_resume(self, file_path, force_update=False):
        """Add resume only if not already processed (unless force_update=True)"""
        try:
            print(f"\n📄 Processing: {file_path}")
            
            # Generate metadata
            metadata, resume_id = self._create_metadata(file_path)
            
            # Check if already processed
            if resume_id in self.processed_resumes and not force_update:
                print(f"⏭️ Resume {resume_id} already exists. Skipping.")
                print("   💡 Use force_update=True to update existing resume")
                return True, resume_id, 0
            
            if resume_id in self.processed_resumes and force_update:
                print(f"🔄 Updating existing resume: {resume_id}")
                print("   ⚠️ Note: Previous version will remain in database")
                print("   💡 For clean updates, use a fresh database")
            else:
                print(f"🆕 Adding new resume: {resume_id}")
            
            # Load and process document
            documents = self._load_document(file_path)
            
            # Split into chunks
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            docs = text_splitter.split_documents(documents)
            
            # Add metadata to chunks
            for i, doc in enumerate(docs):
                doc.metadata.update(metadata)
                doc.metadata["chunk_id"] = i
                doc.metadata["total_chunks"] = len(docs)
                doc.metadata["chunk_preview"] = doc.page_content[:100]
                
                # Add update timestamp if forcing update
                if force_update:
                    doc.metadata["update_timestamp"] = datetime.now().isoformat()
            
            # Add to database
            self.db.add_documents(docs)
            
            # Track as processed
            self.processed_resumes.add(resume_id)
            
            print(f"   ✅ Added {len(docs)} chunks")
            return True, resume_id, len(docs)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False, None, 0
    
    def add_multiple_resumes(self, file_paths, force_update=False):
        """Add multiple resumes"""
        print(f"🔄 Processing {len(file_paths)} resumes...")
        if force_update:
            print("⚠️ Force update enabled - will add even if already exists")
        
        results = []
        total_new_chunks = 0
        
        for file_path in file_paths:
            success, resume_id, chunks = self.add_resume(file_path, force_update)
            results.append({
                'file': file_path,
                'success': success,
                'resume_id': resume_id,
                'chunks': chunks
            })
            if success:
                total_new_chunks += chunks
        
        successful = [r for r in results if r['success']]
        print(f"\n📊 Summary:")
        print(f"   Files processed: {len(file_paths)}")
        print(f"   Successful: {len(successful)}")
        print(f"   New chunks added: {total_new_chunks}")
        
        return results
    
    def list_resumes(self):
        """List all resumes"""
        try:
            all_docs = self.db.similarity_search("", k=1000)
            
            resume_stats = {}
            for doc in all_docs:
                resume_id = doc.metadata.get('Resume_ID')
                if resume_id not in resume_stats:
                    resume_stats[resume_id] = {
                        'resume_id': resume_id,
                        'document_name': doc.metadata.get('document_name'),
                        'file_format': doc.metadata.get('file_format'),
                        'file_path': doc.metadata.get('file_path'),
                        'processed_date': doc.metadata.get('processed_date'),
                        'chunks': 0
                    }
                resume_stats[resume_id]['chunks'] += 1
            
            return list(resume_stats.values())
            
        except Exception as e:
            print(f"❌ Error listing: {e}")
            return []
    
    def search(self, query, resume_id=None, k=5):
        """Search resumes"""
        try:
            if resume_id:
                results = self.db.similarity_search(
                    query, k=k, filter={"Resume_ID": resume_id}
                )
            else:
                results = self.db.similarity_search(query, k=k)
            
            return results
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def get_stats(self):
        """Get database statistics"""
        resumes = self.list_resumes()
        total_chunks = sum(r['chunks'] for r in resumes)
        
        return {
            'total_resumes': len(resumes),
            'total_chunks': total_chunks,
            'processed_resume_ids': list(self.processed_resumes),
            'resumes': resumes
        }

def demo_no_duplicate_functionality():
    """Demonstrate no-duplicate functionality"""
    print("=== Demo: Resume DB with No-Duplicate Logic ===\n")
    
    # Create fresh database
    db = UpdateableResumeDB()
    
    files = [
        "./data/Brandon_Tobalski_1-28-2022.pdf",
        "./data/Brandon_Tobalski_1-28-2022.docx"
    ]
    
    print("🟢 FIRST RUN - Adding resumes:")
    results1 = db.add_multiple_resumes(files)
    
    stats1 = db.get_stats()
    print(f"\nAfter first run:")
    print(f"   Resumes: {stats1['total_resumes']}")
    print(f"   Chunks: {stats1['total_chunks']}")
    
    print("\n🟡 SECOND RUN - Same files (should skip):")
    results2 = db.add_multiple_resumes(files)
    
    stats2 = db.get_stats()
    print(f"\nAfter second run:")
    print(f"   Resumes: {stats2['total_resumes']}")
    print(f"   Chunks: {stats2['total_chunks']}")
    
    print("\n🔵 THIRD RUN - Force update:")
    results3 = db.add_multiple_resumes(files, force_update=True)
    
    stats3 = db.get_stats()
    print(f"\nAfter force update:")
    print(f"   Resumes: {stats3['total_resumes']}")
    print(f"   Chunks: {stats3['total_chunks']}")
    
    print("\n✅ VERIFICATION:")
    if stats1['total_chunks'] == stats2['total_chunks']:
        print("✅ SUCCESS: No duplicates on second run!")
    else:
        print("❌ Issue: Duplicates were created")
    
    if stats3['total_chunks'] > stats2['total_chunks']:
        print("✅ SUCCESS: Force update added new versions!")
    
    # Show resume list
    print(f"\n📋 Final resume list:")
    for resume in stats3['resumes']:
        print(f"   - {resume['document_name']}: {resume['chunks']} chunks")
    
    # Test search
    print(f"\n🔍 Search test:")
    results = db.search("cybersecurity certifications", k=2)
    print(f"Found {len(results)} results")
    
    return db

if __name__ == "__main__":
    # Run demonstration
    demo_db = demo_no_duplicate_functionality()