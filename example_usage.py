"""
Example usage of the ChromaDB RAG system.

This script demonstrates:
1. Loading documents from a directory
2. Creating embeddings and storing in ChromaDB
3. Performing similarity search
4. Using the QA chain to answer questions
"""

import os
from dotenv import load_dotenv
from rag_chromadb import ChromaDBRAG


def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not found in environment variables.")
        print("Please set it in a .env file or as an environment variable.")
        return
    
    # Initialize the RAG system
    print("=" * 50)
    print("Initializing ChromaDB RAG System")
    print("=" * 50)
    
    rag = ChromaDBRAG(
        persist_directory="./chroma_db",
        collection_name="example_collection"
    )
    
    # Example 1: Create a new vector store from documents
    print("\n" + "=" * 50)
    print("Example 1: Creating Vector Store from Documents")
    print("=" * 50)
    
    # Load documents from the sample_documents directory
    documents_path = "./sample_documents"
    
    if os.path.exists(documents_path):
        # Load documents
        documents = rag.load_documents(documents_path, glob_pattern="**/*.txt")
        
        # Split documents into chunks
        chunks = rag.split_documents(documents, chunk_size=500, chunk_overlap=50)
        
        # Create vector store
        rag.create_vectorstore(chunks)
    else:
        print(f"Directory {documents_path} not found. Loading existing vector store...")
        
        # Example 2: Load an existing vector store
        print("\n" + "=" * 50)
        print("Example 2: Loading Existing Vector Store")
        print("=" * 50)
        
        try:
            rag.load_vectorstore()
        except Exception as e:
            print(f"Error loading vector store: {e}")
            print("Please create sample documents first.")
            return
    
    # Example 3: Perform similarity search
    print("\n" + "=" * 50)
    print("Example 3: Similarity Search")
    print("=" * 50)
    
    query = "What is artificial intelligence?"
    print(f"\nQuery: {query}")
    
    try:
        results = rag.similarity_search(query, k=3)
        print(f"\nFound {len(results)} similar documents:")
        for i, doc in enumerate(results, 1):
            print(f"\n--- Document {i} ---")
            print(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)
    except Exception as e:
        print(f"Error during similarity search: {e}")
    
    # Example 4: Question Answering with RAG
    print("\n" + "=" * 50)
    print("Example 4: Question Answering with RAG")
    print("=" * 50)
    
    # Set up the QA chain
    rag.setup_qa_chain(llm_model="gpt-3.5-turbo", temperature=0)
    
    questions = [
        "What is artificial intelligence?",
        "What are the main applications of machine learning?",
        "Explain the difference between supervised and unsupervised learning."
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        try:
            response = rag.query(question)
            print(f"Answer: {response['result']}")
            print(f"\nSources used: {len(response['source_documents'])} document(s)")
        except Exception as e:
            print(f"Error: {e}")
    
    # Example 5: Custom prompt template
    print("\n" + "=" * 50)
    print("Example 5: Custom Prompt Template")
    print("=" * 50)
    
    custom_prompt = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Always provide a brief explanation along with your answer.

Context: {context}

Question: {question}

Helpful Answer:"""
    
    question = "What are neural networks?"
    print(f"\nQuestion: {question}")
    
    try:
        response = rag.query_with_custom_prompt(question, custom_prompt)
        print(f"Answer: {response['result']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
