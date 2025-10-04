"""
LangChain RAG (Retrieval-Augmented Generation) using ChromaDB as storage backend.

This module provides a simple interface for:
1. Loading documents from various sources
2. Splitting documents into chunks
3. Creating embeddings and storing them in ChromaDB
4. Querying the vector store for relevant information
5. Using LLM to generate responses based on retrieved context
"""

import os
from typing import List, Optional
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


class ChromaDBRAG:
    """
    A class to handle RAG operations using ChromaDB as the vector store.
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "langchain_collection",
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the ChromaDB RAG system.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the ChromaDB collection
            openai_api_key: OpenAI API key (if not provided, will use OPENAI_API_KEY env var)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Set OpenAI API key
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize vector store (will be set when loading or creating)
        self.vectorstore = None
        self.retriever = None
        self.qa_chain = None
    
    def load_documents(self, source_path: str, glob_pattern: str = "**/*.txt") -> List:
        """
        Load documents from a directory or file.
        
        Args:
            source_path: Path to directory or file
            glob_pattern: Pattern to match files (only used for directories)
            
        Returns:
            List of loaded documents
        """
        if os.path.isdir(source_path):
            loader = DirectoryLoader(
                source_path,
                glob=glob_pattern,
                loader_cls=TextLoader,
                show_progress=True
            )
        else:
            loader = TextLoader(source_path)
        
        documents = loader.load()
        print(f"Loaded {len(documents)} document(s)")
        return documents
    
    def split_documents(
        self,
        documents: List,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List:
        """
        Split documents into chunks.
        
        Args:
            documents: List of documents to split
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of document chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks")
        return chunks
    
    def create_vectorstore(self, documents: List):
        """
        Create and persist a ChromaDB vector store from documents.
        
        Args:
            documents: List of documents to add to the vector store
        """
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name=self.collection_name
        )
        print(f"Created vector store with {len(documents)} documents")
        print(f"Persisted to: {self.persist_directory}")
    
    def load_vectorstore(self):
        """
        Load an existing ChromaDB vector store from disk.
        """
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
        )
        print(f"Loaded vector store from: {self.persist_directory}")
    
    def add_documents(self, documents: List):
        """
        Add documents to an existing vector store.
        
        Args:
            documents: List of documents to add
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call create_vectorstore() or load_vectorstore() first.")
        
        self.vectorstore.add_documents(documents)
        print(f"Added {len(documents)} documents to vector store")
    
    def similarity_search(self, query: str, k: int = 4) -> List:
        """
        Perform similarity search on the vector store.
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call create_vectorstore() or load_vectorstore() first.")
        
        results = self.vectorstore.similarity_search(query, k=k)
        return results
    
    def setup_qa_chain(
        self,
        llm_model: str = "gpt-3.5-turbo",
        temperature: float = 0,
        chain_type: str = "stuff"
    ):
        """
        Set up a question-answering chain with the vector store.
        
        Args:
            llm_model: OpenAI model to use
            temperature: Temperature for LLM responses
            chain_type: Type of chain to use ("stuff", "map_reduce", "refine", "map_rerank")
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call create_vectorstore() or load_vectorstore() first.")
        
        # Initialize LLM
        llm = ChatOpenAI(model_name=llm_model, temperature=temperature)
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        
        # Create QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type=chain_type,
            retriever=self.retriever,
            return_source_documents=True
        )
        print("QA chain initialized")
    
    def query(self, question: str) -> dict:
        """
        Query the RAG system with a question.
        
        Args:
            question: Question to ask
            
        Returns:
            Dictionary with 'result' and 'source_documents'
        """
        if self.qa_chain is None:
            raise ValueError("QA chain not initialized. Call setup_qa_chain() first.")
        
        response = self.qa_chain.invoke({"query": question})
        return response
    
    def query_with_custom_prompt(self, question: str, prompt_template: str) -> dict:
        """
        Query the RAG system with a custom prompt template.
        
        Args:
            question: Question to ask
            prompt_template: Custom prompt template with {context} and {question} placeholders
            
        Returns:
            Dictionary with 'result' and 'source_documents'
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call create_vectorstore() or load_vectorstore() first.")
        
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        response = qa_chain.invoke({"query": question})
        return response
