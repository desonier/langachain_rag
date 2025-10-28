import os
import uuid
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

def clear_chromadb():
    """Clear the existing ChromaDB to start fresh"""
    import shutil
    persist_directory = "./resume_vectordb"
    
    if os.path.exists(persist_directory):
        try:
            shutil.rmtree(persist_directory)
            print("🗑️ Cleared existing ChromaDB")
        except Exception as e:
            print(f"⚠️ Could not clear ChromaDB: {e}")

def load_document(file_path):
    """Load document based on file extension"""
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        return loader.load()
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
        return loader.load()
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

def create_resume_metadata(content, file_path):
    """Extract structured metadata from resume content - ONE ID per file"""
    
    # Create ONE unique Resume_ID per file (not per processing run)
    # Use file path to create consistent ID
    file_name = os.path.basename(file_path)
    # Create a consistent UUID based on file path
    import hashlib
    file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
    
    file_extension = file_path.split('.')[-1].upper()
    metadata = {
        "Resume_ID": f"{file_name}_{file_hash}",  # Consistent ID per file
        "Resume_Date": datetime.now().isoformat(),
        "Source": f"{file_extension} resume",
        "file_path": file_path,
        "content_type": "resume",
        "file_format": file_extension,
        "document_name": file_name
    }
    return metadata

def process_independent_documents():
    """Process multiple resume files as truly independent documents"""
    
    # Clear existing database for clean start
    clear_chromadb()
    
    # List of files to process as independent documents
    file_paths = [
        "./data/Brandon_Tobalski_1-28-2022.pdf",
        "./data/Brandon_Tobalski_1-28-2022.docx"
    ]
    
    print("🔄 Processing independent documents...")
    
    # Create embeddings
    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("EMBEDDING_MODEL")
    )
    
    all_docs = []
    
    for file_path in file_paths:
        try:
            print(f"📄 Processing: {file_path}")
            
            # Load document
            documents = load_document(file_path)
            
            # Extract full text for metadata
            full_text = " ".join([doc.page_content for doc in documents])
            
            # Create consistent metadata for this specific file
            file_metadata = create_resume_metadata(full_text, file_path)
            
            # Split into chunks
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            docs = text_splitter.split_documents(documents)
            
            # Add file-specific metadata to each chunk
            for i, doc in enumerate(docs):
                # Combine original metadata with file metadata
                doc.metadata.update(file_metadata)
                doc.metadata["chunk_id"] = i
                doc.metadata["chunk_content"] = doc.page_content[:100]
                doc.metadata["total_chunks"] = len(docs)
            
            all_docs.extend(docs)
            print(f"   ✅ Added {len(docs)} chunks with Resume_ID: {file_metadata['Resume_ID']}")
            
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")
    
    # Create ChromaDB with all independent documents
    persist_directory = "./resume_vectordb"
    
    db = Chroma.from_documents(
        documents=all_docs,
        embedding=embedding,
        persist_directory=persist_directory
    )
    
    print(f"\n✅ Successfully processed {len(file_paths)} independent documents")
    print(f"📊 Total chunks: {len(all_docs)}")
    
    return db

def test_independence(db):
    """Test that documents are truly independent"""
    
    print("\n=== Testing Document Independence ===")
    
    # Test 1: Search specific document
    print("\n🔍 Test 1: Search only PDF document")
    pdf_results = db.similarity_search(
        "cybersecurity", 
        k=3, 
        filter={"file_format": "PDF"}
    )
    
    print(f"Found {len(pdf_results)} chunks from PDF:")
    for doc in pdf_results:
        resume_id = doc.metadata.get('Resume_ID')
        file_name = doc.metadata.get('document_name')
        print(f"   - {file_name} (ID: {resume_id})")
    
    # Test 2: Search specific document
    print("\n🔍 Test 2: Search only DOCX document")
    docx_results = db.similarity_search(
        "cybersecurity", 
        k=3, 
        filter={"file_format": "DOCX"}
    )
    
    print(f"Found {len(docx_results)} chunks from DOCX:")
    for doc in docx_results:
        resume_id = doc.metadata.get('Resume_ID')
        file_name = doc.metadata.get('document_name')
        print(f"   - {file_name} (ID: {resume_id})")
    
    # Test 3: Get all unique Resume_IDs
    all_docs = db.similarity_search("", k=100)
    unique_ids = set()
    file_counts = {}
    
    for doc in all_docs:
        resume_id = doc.metadata.get('Resume_ID')
        file_name = doc.metadata.get('document_name')
        unique_ids.add(resume_id)
        file_counts[file_name] = file_counts.get(file_name, 0) + 1
    
    print(f"\n📊 Independence Summary:")
    print(f"   Unique Resume_IDs: {len(unique_ids)}")
    print(f"   Resume_IDs: {list(unique_ids)}")
    print(f"   Chunks per file:")
    for file_name, count in file_counts.items():
        print(f"      - {file_name}: {count} chunks")

if __name__ == "__main__":
    # Process documents as truly independent
    db = process_independent_documents()
    
    # Test independence
    test_independence(db)