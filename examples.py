"""
Example usage of LangChain RAG with ChromaDB

This script demonstrates how to use the LangChainRAG class
for various common tasks.
"""

from app import LangChainRAG


def example_1_basic_usage():
    """Example 1: Basic document addition and querying"""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 60)
    
    # Initialize the RAG system
    rag = LangChainRAG(persist_directory="./example_chroma_data")
    
    # Add some documents
    docs = [
        "Python is a high-level programming language known for its simplicity and readability.",
        "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
        "Docker containers provide a lightweight way to package and deploy applications."
    ]
    
    rag.add_documents(docs)
    
    # Query the system
    results = rag.query("What is Python?", k=1)
    print(f"\nQuery: What is Python?")
    print(f"Result: {results[0].page_content}")


def example_2_with_metadata():
    """Example 2: Adding documents with metadata"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Documents with Metadata")
    print("=" * 60)
    
    rag = LangChainRAG(persist_directory="./example_chroma_data")
    
    # Documents with metadata
    docs = [
        "Neural networks are computing systems inspired by biological neural networks.",
        "Deep learning uses multiple layers to progressively extract features from raw input.",
        "Transformers are a type of neural network architecture used in NLP."
    ]
    
    metadata = [
        {"topic": "neural_networks", "category": "basics", "difficulty": "beginner"},
        {"topic": "deep_learning", "category": "advanced", "difficulty": "intermediate"},
        {"topic": "transformers", "category": "architecture", "difficulty": "advanced"}
    ]
    
    rag.add_documents(docs, metadata)
    
    # Query and show metadata
    results = rag.query("Tell me about neural networks", k=2)
    print(f"\nQuery: Tell me about neural networks")
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"  Content: {result.page_content}")
        print(f"  Metadata: {result.metadata}")


def example_3_multiple_queries():
    """Example 3: Multiple queries on the same knowledge base"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Multiple Queries")
    print("=" * 60)
    
    rag = LangChainRAG(persist_directory="./example_chroma_data")
    
    # Add documents about various topics
    docs = [
        "Git is a distributed version control system for tracking changes in source code.",
        "GitHub is a web-based platform for version control and collaboration.",
        "Docker enables developers to package applications into containers.",
        "Kubernetes is an open-source system for automating deployment and scaling of containers.",
        "CI/CD stands for Continuous Integration and Continuous Deployment."
    ]
    
    rag.add_documents(docs)
    
    # Multiple queries
    queries = [
        "What is version control?",
        "How do containers work?",
        "What is CI/CD?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = rag.query(query, k=1)
        if results:
            print(f"Answer: {results[0].page_content}")


def example_4_persistent_storage():
    """Example 4: Demonstrating persistence across sessions"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Persistent Storage")
    print("=" * 60)
    
    persist_dir = "./example_persistent_chroma"
    
    # First session: Add documents
    print("\n--- Session 1: Adding documents ---")
    rag1 = LangChainRAG(persist_directory=persist_dir)
    docs = [
        "ChromaDB is an AI-native open-source embedding database.",
        "Vector databases store high-dimensional vectors and enable similarity search."
    ]
    rag1.add_documents(docs)
    print("Documents added and persisted to disk")
    
    # Second session: Query existing data
    print("\n--- Session 2: Querying persisted data ---")
    rag2 = LangChainRAG(persist_directory=persist_dir)
    results = rag2.query("What is ChromaDB?", k=1)
    print(f"Query: What is ChromaDB?")
    print(f"Result from persisted data: {results[0].page_content}")


def example_5_similarity_scores():
    """Example 5: Working with similarity scores"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Similarity Scores")
    print("=" * 60)
    
    rag = LangChainRAG(persist_directory="./example_chroma_data")
    
    # Add documents
    docs = [
        "Artificial Intelligence is the simulation of human intelligence by machines.",
        "Machine Learning is a method of data analysis that automates model building.",
        "Natural Language Processing enables computers to understand human language.",
        "Computer Vision gives machines the ability to interpret visual information."
    ]
    
    rag.add_documents(docs)
    
    # Use similarity_search_with_score
    query = "AI and intelligent systems"
    results = rag.vectorstore.similarity_search_with_score(query, k=3)
    
    print(f"\nQuery: {query}")
    print("\nResults with similarity scores:")
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n  {i}. Score: {score:.4f}")
        print(f"     Content: {doc.page_content}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("LangChain RAG with ChromaDB - Usage Examples")
    print("=" * 60)
    
    examples = [
        example_1_basic_usage,
        example_2_with_metadata,
        example_3_multiple_queries,
        example_4_persistent_storage,
        example_5_similarity_scores
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nError in {example_func.__name__}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
    print("\nNote: Example data directories have been created.")
    print("You can delete them with: rm -rf example_*")


if __name__ == "__main__":
    main()
