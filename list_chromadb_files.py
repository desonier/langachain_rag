import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb
from collections import defaultdict

# Load environment variables
load_dotenv()

def list_chromadb_contents():
    """List all files and documents stored in ChromaDB"""
    
    print("=== ChromaDB Vector Database Contents ===\n")
    
    # Create Azure OpenAI embeddings (needed to access the vector store)
    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("EMBEDDING_MODEL")
    )
    
    # Connect to existing ChromaDB
    persist_directory = "./chroma_store"
    
    try:
        # Load existing vector store
        db = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding
        )
        
        # Get all documents from the collection
        collection = db._collection
        all_data = collection.get(include=['documents', 'metadatas', 'ids'])
        
        total_documents = len(all_data['ids'])
        print(f"📊 Total documents in ChromaDB: {total_documents}\n")
        
        if total_documents == 0:
            print("❌ No documents found in ChromaDB")
            return
        
        # Group documents by source file
        files_data = defaultdict(list)
        
        for i, doc_id in enumerate(all_data['ids']):
            metadata = all_data['metadatas'][i]
            document = all_data['documents'][i]
            
            # Get source file from metadata
            source_file = metadata.get('file_path', metadata.get('source', 'Unknown'))
            files_data[source_file].append({
                'id': doc_id,
                'metadata': metadata,
                'content_preview': document[:100] + "..." if len(document) > 100 else document
            })
        
        # Display files and their chunks
        print("📁 Files in Vector Database:\n")
        
        for file_path, chunks in files_data.items():
            print(f"📄 File: {file_path}")
            print(f"   📊 Number of chunks: {len(chunks)}")
            
            # Show metadata from first chunk
            first_chunk = chunks[0]
            metadata = first_chunk['metadata']
            
            print(f"   📋 Metadata:")
            for key, value in metadata.items():
                if key not in ['chunk_content']:  # Skip content preview in metadata
                    print(f"      {key}: {value}")
            
            print(f"   📝 Document chunks:")
            for j, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                print(f"      Chunk {j+1}: {chunk['content_preview']}")
            
            if len(chunks) > 3:
                print(f"      ... and {len(chunks) - 3} more chunks")
            
            print("-" * 80)
        
        # Show collection statistics
        print("\n📈 Collection Statistics:")
        file_formats = defaultdict(int)
        content_types = defaultdict(int)
        
        for metadata in all_data['metadatas']:
            file_format = metadata.get('file_format', 'Unknown')
            content_type = metadata.get('content_type', 'Unknown')
            file_formats[file_format] += 1
            content_types[content_type] += 1
        
        print("   File Formats:")
        for format_type, count in file_formats.items():
            print(f"      {format_type}: {count} chunks")
        
        print("   Content Types:")
        for content_type, count in content_types.items():
            print(f"      {content_type}: {count} chunks")
            
    except Exception as e:
        print(f"❌ Error accessing ChromaDB: {e}")
        print("Make sure the ChromaDB directory exists and contains data.")

def list_collections():
    """List all collections in ChromaDB"""
    print("\n🗂️  Available Collections:\n")
    
    try:
        # Direct ChromaDB client access
        client = chromadb.PersistentClient(path="./chroma_store")
        collections = client.list_collections()
        
        if not collections:
            print("❌ No collections found")
            return
            
        for collection in collections:
            print(f"📁 Collection: {collection.name}")
            print(f"   ID: {collection.id}")
            
            # Get collection count
            count = collection.count()
            print(f"   Documents: {count}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error listing collections: {e}")

def search_by_metadata(filter_criteria):
    """Search documents by metadata criteria"""
    print(f"\n🔍 Searching by metadata: {filter_criteria}\n")
    
    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("EMBEDDING_MODEL")
    )
    
    try:
        db = Chroma(
            persist_directory="./chroma_store",
            embedding_function=embedding
        )
        
        # Search with metadata filter
        results = db.similarity_search("", k=10, filter=filter_criteria)
        
        print(f"📊 Found {len(results)} documents matching criteria:")
        
        for i, doc in enumerate(results):
            print(f"\n📄 Document {i+1}:")
            print(f"   Content: {doc.page_content[:150]}...")
            print(f"   Metadata: {doc.metadata}")
            
    except Exception as e:
        print(f"❌ Error searching: {e}")

if __name__ == "__main__":
    # List all documents and files
    list_chromadb_contents()
    
    # List collections
    list_collections()
    
    # Example metadata searches
    print("\n" + "="*80)
    print("🔍 Example Metadata Searches:")
    
    # Search by content type
    search_by_metadata({"content_type": "resume"})
    
    # Search by file format
    search_by_metadata({"file_format": "DOCX"})