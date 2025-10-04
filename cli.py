#!/usr/bin/env python3
"""
Command-line interface for the ChromaDB RAG system.

Usage:
    python cli.py create <documents_dir>        # Create a new vector store
    python cli.py load                          # Load existing vector store
    python cli.py query "<question>"            # Ask a question
    python cli.py search "<query>"              # Similarity search
"""

import sys
import argparse
from dotenv import load_dotenv
from rag_chromadb import ChromaDBRAG


def create_vectorstore(args):
    """Create a new vector store from documents"""
    print(f"Creating vector store from: {args.documents_dir}")
    
    rag = ChromaDBRAG(
        persist_directory=args.persist_dir,
        collection_name=args.collection
    )
    
    # Load documents
    documents = rag.load_documents(args.documents_dir, glob_pattern="**/*.txt")
    
    # Split into chunks
    chunks = rag.split_documents(
        documents,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    
    # Create vector store
    rag.create_vectorstore(chunks)
    print(f"\n✅ Vector store created successfully!")
    print(f"   Location: {args.persist_dir}")
    print(f"   Collection: {args.collection}")


def query_rag(args):
    """Query the RAG system"""
    print(f"Loading vector store from: {args.persist_dir}")
    
    rag = ChromaDBRAG(
        persist_directory=args.persist_dir,
        collection_name=args.collection
    )
    
    # Load existing vector store
    rag.load_vectorstore()
    
    # Set up QA chain
    rag.setup_qa_chain(
        llm_model=args.model,
        temperature=args.temperature
    )
    
    # Query
    print(f"\nQuestion: {args.question}")
    print("-" * 50)
    
    response = rag.query(args.question)
    
    print(f"\nAnswer:\n{response['result']}\n")
    
    if args.show_sources:
        print(f"\nSources ({len(response['source_documents'])} documents):")
        for i, doc in enumerate(response['source_documents'], 1):
            print(f"\n--- Source {i} ---")
            print(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)


def similarity_search(args):
    """Perform similarity search"""
    print(f"Loading vector store from: {args.persist_dir}")
    
    rag = ChromaDBRAG(
        persist_directory=args.persist_dir,
        collection_name=args.collection
    )
    
    # Load existing vector store
    rag.load_vectorstore()
    
    # Search
    print(f"\nQuery: {args.query}")
    print("-" * 50)
    
    results = rag.similarity_search(args.query, k=args.k)
    
    print(f"\nFound {len(results)} similar documents:\n")
    
    for i, doc in enumerate(results, 1):
        print(f"--- Document {i} ---")
        print(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)
        print()


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="CLI for ChromaDB RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--persist-dir",
        default="./chroma_db",
        help="Directory to persist ChromaDB data (default: ./chroma_db)"
    )
    
    parser.add_argument(
        "--collection",
        default="langchain_collection",
        help="ChromaDB collection name (default: langchain_collection)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new vector store")
    create_parser.add_argument("documents_dir", help="Directory containing documents")
    create_parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Size of text chunks (default: 1000)"
    )
    create_parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Overlap between chunks (default: 200)"
    )
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the RAG system")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.add_argument(
        "--model",
        default="gpt-3.5-turbo",
        help="OpenAI model to use (default: gpt-3.5-turbo)"
    )
    query_parser.add_argument(
        "--temperature",
        type=float,
        default=0,
        help="Temperature for LLM (default: 0)"
    )
    query_parser.add_argument(
        "--show-sources",
        action="store_true",
        help="Show source documents used for the answer"
    )
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Perform similarity search")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-k",
        type=int,
        default=4,
        help="Number of results to return (default: 4)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "create":
            create_vectorstore(args)
        elif args.command == "query":
            query_rag(args)
        elif args.command == "search":
            similarity_search(args)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
