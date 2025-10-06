from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

# Create embeddings
embedding = AzureOpenAIEmbeddings(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    model=os.getenv("EMBEDDING_MODEL")
)

# Load database
db = Chroma(
    persist_directory="./resume_vectordb",
    embedding_function=embedding
)

print("🔍 Analyzing LLM-Enhanced Database Structure")
print("=" * 50)

# Get all documents
all_docs = db.similarity_search("", k=20)

print(f"📊 Total chunks in database: {len(all_docs)}")

# Analyze metadata structure
if all_docs:
    print(f"\n📋 Sample Metadata from First Chunk:")
    first_doc = all_docs[0]
    for key, value in first_doc.metadata.items():
        print(f"   {key}: {value}")
    
    print(f"\n📄 Sample Content Preview:")
    print(f"   {first_doc.page_content[:200]}...")
    
    # Check for LLM-extracted fields
    print(f"\n🤖 LLM-Extracted Fields Found:")
    llm_fields = ['candidate_name', 'key_skills', 'experience_years', 'certifications', 'education', 'contact_info']
    
    for doc in all_docs[:2]:  # Check first 2 documents
        print(f"\n   Resume: {doc.metadata.get('document_name', 'Unknown')}")
        for field in llm_fields:
            if field in doc.metadata:
                value = doc.metadata[field]
                print(f"     ✅ {field}: {value}")
            else:
                print(f"     ❌ {field}: Not found")
        
        # Check parsing method
        parsing_method = doc.metadata.get('parsing_method', 'unknown')
        chunk_type = doc.metadata.get('chunk_type', 'unknown')
        section_name = doc.metadata.get('section_name', 'N/A')
        print(f"     📝 Parsing: {parsing_method}, Type: {chunk_type}, Section: {section_name}")

print("\n" + "=" * 50)
print("✅ Database analysis complete!")