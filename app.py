"""
LangChain RAG application with ChromaDB integration.
This application demonstrates document ingestion, embedding, and retrieval using LangChain and ChromaDB.
"""

import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document

# Load environment variables
load_dotenv()


class LangChainRAG:
    """LangChain RAG system with ChromaDB backend."""

    def __init__(self, persist_directory="./chroma_data"):
        """
        Initialize the RAG system.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        
        # Initialize embeddings using HuggingFace (no API key needed)
        print("Initializing embeddings...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize ChromaDB vector store
        print(f"Initializing ChromaDB at {persist_directory}...")
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings,
            collection_name="langchain_collection"
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def add_documents(self, texts, metadatas=None):
        """
        Add documents to the vector store.
        
        Args:
            texts: List of text strings to add
            metadatas: Optional list of metadata dictionaries
        """
        print(f"Adding {len(texts)} documents...")
        
        # Create Document objects
        documents = [Document(page_content=text, metadata=metadatas[i] if metadatas else {}) 
                    for i, text in enumerate(texts)]
        
        # Split documents into chunks
        split_docs = self.text_splitter.split_documents(documents)
        print(f"Split into {len(split_docs)} chunks")
        
        # Add to vector store
        self.vectorstore.add_documents(split_docs)
        print("Documents added successfully!")

    def query(self, question, k=3):
        """
        Query the vector store and return relevant documents.
        
        Args:
            question: Question to search for
            k: Number of documents to return
            
        Returns:
            List of relevant documents
        """
        print(f"Searching for: {question}")
        results = self.vectorstore.similarity_search(question, k=k)
        return results

    def create_qa_chain(self, llm=None):
        """
        Create a QA chain using the vector store as retriever.
        
        Args:
            llm: Language model to use (optional)
            
        Returns:
            RetrievalQA chain
        """
        if llm is None:
            # Use OpenAI by default if API key is available
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                llm = OpenAI(temperature=0)
            else:
                print("Warning: No OPENAI_API_KEY found. QA chain requires an LLM.")
                return None
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
        return qa_chain


def main():
    """Main function to demonstrate the RAG system."""
    print("=" * 60)
    print("LangChain RAG with ChromaDB Demo")
    print("=" * 60)
    
    # Initialize RAG system
    rag = LangChainRAG()
    
    # Sample documents to add
    sample_docs = [
        "LangChain is a framework for developing applications powered by language models. It enables applications that are context-aware and can reason.",
        "ChromaDB is an open-source embedding database. It makes it easy to build LLM apps by making knowledge, facts, and skills pluggable for LLMs.",
        "Docker is a platform for developing, shipping, and running applications in containers. Containers allow developers to package applications with all dependencies.",
        "Retrieval Augmented Generation (RAG) is a technique that combines retrieval of relevant documents with text generation to provide more accurate and contextual responses.",
        "Vector databases store embeddings and enable efficient similarity search. They are essential for building semantic search and RAG applications."
    ]
    
    metadatas = [
        {"source": "langchain_docs", "topic": "framework"},
        {"source": "chromadb_docs", "topic": "database"},
        {"source": "docker_docs", "topic": "containers"},
        {"source": "ai_concepts", "topic": "rag"},
        {"source": "ai_concepts", "topic": "vector_db"}
    ]
    
    # Add documents
    rag.add_documents(sample_docs, metadatas)
    
    print("\n" + "=" * 60)
    print("Querying the knowledge base")
    print("=" * 60)
    
    # Query examples
    queries = [
        "What is LangChain?",
        "Tell me about vector databases",
        "What is ChromaDB used for?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = rag.query(query, k=2)
        print(f"Found {len(results)} relevant documents:")
        for i, doc in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"  Content: {doc.page_content[:100]}...")
            print(f"  Metadata: {doc.metadata}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
