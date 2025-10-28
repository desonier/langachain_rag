import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb
from collections import defaultdict, Counter

# Load environment variables
load_dotenv()

def get_chromadb_summary():
    """Get a summary of files in ChromaDB"""
    
    print("=== ChromaDB Files Summary ===\n")
    
    # Create Azure OpenAI embeddings
    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("EMBEDDING_MODEL")
    )
    
    try:
        # Connect to ChromaDB
        db = Chroma(
            persist_directory="./resume_vectordb",
            embedding_function=embedding
        )
        
        # Get all documents
        results = db.similarity_search("", k=100)  # Get up to 100 documents
        
        if not results:
            print("❌ No documents found in ChromaDB")
            return
        
        print(f"📊 Total documents: {len(results)}")
        
        # Analyze files
        files = defaultdict(list)
        file_formats = Counter()
        sources = Counter()
        
        for doc in results:
            metadata = doc.metadata
            file_path = metadata.get('file_path', metadata.get('source', 'Unknown'))
            files[file_path].append(doc)
            
            file_format = metadata.get('file_format', 'Unknown')
            file_formats[file_format] += 1
            
            source = metadata.get('Source', 'Unknown')
            sources[source] += 1
        
        # Display file summary
        print(f"\n📁 Unique files: {len(files)}")
        print("\n📄 Files in database:")
        
        for file_path, docs in files.items():
            print(f"   • {file_path} ({len(docs)} chunks)")
        
        print(f"\n📊 File formats:")
        for format_type, count in file_formats.items():
            print(f"   • {format_type}: {count} chunks")
        
        print(f"\n📋 Document sources:")
        for source, count in sources.items():
            print(f"   • {source}: {count} chunks")
        
        # Show collection info
        client = chromadb.PersistentClient(path="./resume_vectordb")
        collections = client.list_collections()
        
        print(f"\n🗂️  Collections: {len(collections)}")
        for collection in collections:
            print(f"   • {collection.name}: {collection.count()} documents")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def list_specific_file_chunks(file_name):
    """List chunks for a specific file"""
    print(f"\n=== Chunks for: {file_name} ===\n")
    
    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model=os.getenv("EMBEDDING_MODEL")
    )
    
    try:
        db = Chroma(
            persist_directory="./resume_vectordb",
            embedding_function=embedding
        )
        
        # Search for documents containing the file name
        results = db.similarity_search("", k=100)
        
        file_docs = [doc for doc in results if file_name in doc.metadata.get('file_path', '')]
        
        if not file_docs:
            print(f"❌ No chunks found for file: {file_name}")
            return
            
        print(f"📊 Found {len(file_docs)} chunks")
        
        # Sort by chunk_id if available
        try:
            file_docs.sort(key=lambda x: x.metadata.get('chunk_id', 0))
        except:
            pass
        
        for i, doc in enumerate(file_docs):
            chunk_id = doc.metadata.get('chunk_id', i)
            print(f"\n📄 Chunk {chunk_id + 1}:")
            print(f"   Content: {doc.page_content[:200]}...")
            print(f"   Metadata keys: {list(doc.metadata.keys())}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Get overall summary
    get_chromadb_summary()
    
    # List chunks for specific files
    print("\n" + "="*60)
    list_specific_file_chunks("Brandon_Tobalski_1-28-2022.docx")
    
    print("\n" + "="*60)
    list_specific_file_chunks("Brandon_Tobalski_1-28-2022.pdf")