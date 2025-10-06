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

# Function to load documents based on file extension
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

# Resume schema adapted for ChromaDB metadata
def create_resume_metadata(content, file_path):
    """Extract structured metadata from resume content"""
    
    # Use LLM to extract structured information
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        deployment_name=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
    )
    
    # Extraction prompt
    extraction_prompt = f"""
    Extract the following information from this resume text. If information is not found, use "Not specified":
    
    Resume Text:
    {content[:2000]}  # Limit content for prompt
    
    Please extract and format as JSON:
    {{
        "Name": "Full name of the person",
        "Location": "City, State or location mentioned",
        "Phone": "Phone number if mentioned",
        "Email": "Email address if mentioned",
        "Clearance_Level": "Security clearance level (e.g., TS/SCI, Secret, etc.)",
        "Education": "Education background summary",
        "Certifications": "List of certifications",
        "Skills": "Key skills and technologies",
        "Professional_Experience": "Work experience summary",
        "Source": "Document resume"
    }}
    """
    
    try:
        response = llm.invoke(extraction_prompt)
        # For now, create basic metadata
        file_extension = file_path.split('.')[-1].upper()
        metadata = {
            "Resume_ID": str(uuid.uuid4()),
            "Resume_Date": datetime.now().isoformat(),
            "Source": f"{file_extension} resume",
            "file_path": file_path,
            "content_type": "resume",
            "file_format": file_extension
        }
        return metadata
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        file_extension = file_path.split('.')[-1].upper()
        return {
            "Resume_ID": str(uuid.uuid4()),
            "Resume_Date": datetime.now().isoformat(),
            "Source": f"{file_extension} resume",
            "file_path": file_path,
            "content_type": "resume",
            "file_format": file_extension
        }

# Load your document (automatically detects PDF or DOCX)
# You can change this to process either PDF or DOCX
file_path = "./data/Brandon_Tobalski_1-28-2022.docx"  # Changed to DOCX
# file_path = "./data/Brandon_Tobalski_1-28-2022.pdf"  # Uncomment for PDF

print(f"Loading document: {file_path}")
documents = load_document(file_path)
print(f"Successfully loaded {len(documents)} document(s)")

# Function to process multiple files
def process_multiple_files(file_paths):
    """Process multiple resume files and combine them"""
    all_documents = []
    for fp in file_paths:
        try:
            docs = load_document(fp)
            # Add file info to each document
            for doc in docs:
                doc.metadata["source_file"] = fp
            all_documents.extend(docs)
            print(f"Loaded: {fp}")
        except Exception as e:
            print(f"Error loading {fp}: {e}")
    return all_documents

# Uncomment below to process both PDF and DOCX files
# file_paths = [
#     "./data/Brandon_Tobalski_1-28-2022.pdf",
#     "./data/Brandon_Tobalski_1-28-2022.docx"
# ]
# documents = process_multiple_files(file_paths)

# Extract full text for metadata extraction
full_text = " ".join([doc.page_content for doc in documents])

# Create metadata for the resume
resume_metadata = create_resume_metadata(full_text, file_path)

# Split into chunks
text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = text_splitter.split_documents(documents)

# Add structured metadata to each chunk
for i, doc in enumerate(docs):
    # Combine original metadata with resume metadata
    doc.metadata.update(resume_metadata)
    doc.metadata["chunk_id"] = i
    doc.metadata["chunk_content"] = doc.page_content[:100]  # First 100 chars for filtering

# Create Azure OpenAI embeddings
embedding = AzureOpenAIEmbeddings(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    model=os.getenv("EMBEDDING_MODEL")
)

# Define persistent ChromaDB directory
persist_directory = "./chroma_store"

# Create or load ChromaDB with persistence and metadata
db = Chroma.from_documents(
    documents=docs,
    embedding=embedding,
    persist_directory=persist_directory
)

# Create Azure OpenAI LLM
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    deployment_name=os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
)

# Enhanced retriever with metadata filtering capabilities
# ChromaDB supports vector search natively
retriever = db.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 4,  # Number of documents to retrieve
        "filter": {"content_type": "resume"}  # Metadata filtering
    }
)

# Alternative: Multi-query retriever for semantic-like search
from langchain.retrievers.multi_query import MultiQueryRetriever
multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=retriever, 
    llm=llm
)

# Build RAG pipeline with enhanced retrieval
qa_chain = RetrievalQA.from_chain_type(
    llm=llm, 
    retriever=multi_query_retriever,  # Using multi-query for better semantic search
    return_source_documents=True
)

# Function to search by specific metadata fields
def search_by_metadata(query, metadata_filter=None):
    """Search with optional metadata filtering"""
    if metadata_filter:
        filtered_retriever = db.as_retriever(
            search_kwargs={
                "k": 4,
                "filter": metadata_filter
            }
        )
        filtered_qa_chain = RetrievalQA.from_chain_type(
            llm=llm, 
            retriever=filtered_retriever,
            return_source_documents=True
        )
        return filtered_qa_chain.invoke({"query": query})
    else:
        return qa_chain.invoke({"query": query})

# Test basic search
print("=== Basic Resume Analysis ===")
query = "What is this PDF about?"
response = search_by_metadata(query)
print(f"Query: {query}")
print(f"Answer: {response['result']}")

# Test metadata-based search
print("\n=== Metadata-Based Search ===")
query2 = "What certifications does this person have?"
response2 = search_by_metadata(query2, {"content_type": "resume"})
print(f"Query: {query2}")
print(f"Answer: {response2['result']}")

# Show metadata from retrieved documents
print("\n=== Document Metadata ===")
if 'source_documents' in response2:
    for i, doc in enumerate(response2['source_documents'][:2]):
        print(f"Document {i+1} metadata: {doc.metadata}")
        print(f"Content preview: {doc.page_content[:100]}...")
        print("---")