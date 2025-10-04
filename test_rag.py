"""
Simple test script to verify the ChromaDB RAG implementation.
This script tests the basic functionality without requiring an OpenAI API key.
"""

import os
import sys
from rag_chromadb import ChromaDBRAG


def test_initialization():
    """Test ChromaDBRAG initialization"""
    print("Testing initialization...")
    try:
        rag = ChromaDBRAG(
            persist_directory="./test_chroma_db",
            collection_name="test_collection"
        )
        print("✓ Initialization successful")
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_document_loading():
    """Test document loading"""
    print("\nTesting document loading...")
    try:
        rag = ChromaDBRAG()
        
        if not os.path.exists("./sample_documents"):
            print("✗ Sample documents directory not found")
            return False
        
        documents = rag.load_documents("./sample_documents", glob_pattern="**/*.txt")
        
        if len(documents) > 0:
            print(f"✓ Loaded {len(documents)} documents successfully")
            return True
        else:
            print("✗ No documents loaded")
            return False
    except Exception as e:
        print(f"✗ Document loading failed: {e}")
        return False


def test_document_splitting():
    """Test document splitting"""
    print("\nTesting document splitting...")
    try:
        rag = ChromaDBRAG()
        documents = rag.load_documents("./sample_documents", glob_pattern="**/*.txt")
        chunks = rag.split_documents(documents, chunk_size=500, chunk_overlap=50)
        
        if len(chunks) > len(documents):
            print(f"✓ Split {len(documents)} documents into {len(chunks)} chunks")
            return True
        else:
            print("✗ Document splitting may not be working correctly")
            return False
    except Exception as e:
        print(f"✗ Document splitting failed: {e}")
        return False


def test_vectorstore_operations():
    """Test vector store creation and loading (requires OpenAI API key)"""
    print("\nTesting vector store operations...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠ Skipping vector store tests (OPENAI_API_KEY not set)")
        return True
    
    try:
        rag = ChromaDBRAG(persist_directory="./test_chroma_db")
        documents = rag.load_documents("./sample_documents", glob_pattern="**/*.txt")
        chunks = rag.split_documents(documents, chunk_size=500, chunk_overlap=50)
        
        # Create vector store
        rag.create_vectorstore(chunks)
        print("✓ Vector store created successfully")
        
        # Test loading vector store
        rag2 = ChromaDBRAG(persist_directory="./test_chroma_db")
        rag2.load_vectorstore()
        print("✓ Vector store loaded successfully")
        
        # Clean up
        import shutil
        if os.path.exists("./test_chroma_db"):
            shutil.rmtree("./test_chroma_db")
        
        return True
    except Exception as e:
        print(f"✗ Vector store operations failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("Running ChromaDB RAG Tests")
    print("=" * 50)
    
    tests = [
        test_initialization,
        test_document_loading,
        test_document_splitting,
        test_vectorstore_operations
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
