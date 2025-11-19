"""
ChromaDB Factory - Provides consistent ChromaDB initialization with timeout handling
"""
import os
from pathlib import Path
import threading
import queue
import time

# Global lock for thread-safe initialization
_init_lock = threading.Lock()
_instances = {}  # Cache for ChromaDB instances

def get_embedding_function():
    """Get the embedding function from shared config"""
    try:
        # Try the langchain_huggingface approach first (newer)
        from langchain_huggingface import HuggingFaceEmbeddings
        from shared_config import get_embedding_config
        
        embedding_config = get_embedding_config()
        print(f"🔧 Using HuggingFace embeddings: {embedding_config['model_name']}")
        return HuggingFaceEmbeddings(
            model_name=embedding_config["model_name"],
            model_kwargs=embedding_config["model_kwargs"],
            encode_kwargs=embedding_config["encode_kwargs"]
        )
    except ImportError as e1:
        try:
            # Fallback to langchain_community approach
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from shared_config import get_embedding_config
            
            embedding_config = get_embedding_config()
            print(f"🔧 Using HuggingFace embeddings (community): {embedding_config['model_name']}")
            return HuggingFaceEmbeddings(
                model_name=embedding_config["model_name"],
                model_kwargs=embedding_config["model_kwargs"],
                encode_kwargs=embedding_config["encode_kwargs"]
            )
        except ImportError as e2:
            print(f"⚠️ langchain HuggingFace packages not available: {e1}, {e2}")
            # Try sentence-transformers directly
            try:
                from sentence_transformers import SentenceTransformer
                from shared_config import config
                
                print(f"🔧 Using SentenceTransformer directly: {config.embedding_model}")
                
                # Create a wrapper that mimics the LangChain embedding interface
                class SentenceTransformerEmbeddings:
                    def __init__(self, model_name):
                        self.model = SentenceTransformer(model_name)
                    
                    def embed_documents(self, texts):
                        return self.model.encode(texts).tolist()
                    
                    def embed_query(self, text):
                        return self.model.encode([text])[0].tolist()
                
                return SentenceTransformerEmbeddings(config.embedding_model)
            except Exception as e3:
                print(f"⚠️ SentenceTransformer approach failed: {e3}")
                # Final fallback: Create a dummy embedding function for development
                print("⚠️ No embedding models available. Creating dummy embeddings for development.")
                
                class DummyEmbeddings:
                    def __init__(self):
                        self.dimensions = 384  # Standard dimension for all-MiniLM-L6-v2
                        
                    def embed_documents(self, texts):
                        # Create dummy embeddings with consistent dimensions
                        import random
                        random.seed(42)  # For reproducible results
                        return [[random.random() for _ in range(self.dimensions)] for _ in texts]
                    
                    def embed_query(self, text):
                        import random
                        random.seed(hash(text) % 1000)  # Consistent per query
                        return [random.random() for _ in range(self.dimensions)]
                
                return DummyEmbeddings()

def _init_chromadb_with_timeout(persist_directory, collection_name, embedding_function, timeout=15):
    """Initialize ChromaDB with timeout handling"""
    result_queue = queue.Queue()
    exception_queue = queue.Queue()
    
    def init_worker():
        try:
            # Try the newer langchain_chroma first
            try:
                from langchain_chroma import Chroma
                print("🔧 Using newer langchain_chroma package")
            except ImportError:
                # Fallback to langchain_community
                from langchain_community.vectorstores import Chroma
                print("🔧 Using langchain_community Chroma")
            
            print(f"🔧 Initializing ChromaDB at: {persist_directory}")
            if collection_name:
                print(f"📂 Using collection: {collection_name}")
            
            # Create ChromaDB with minimal settings
            if collection_name:
                db = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=embedding_function,
                    collection_name=collection_name
                )
            else:
                db = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=embedding_function
                )
            
            result_queue.put(db)
            
        except Exception as e:
            exception_queue.put(e)
    
    # Start initialization in separate thread
    init_thread = threading.Thread(target=init_worker)
    init_thread.daemon = True
    init_thread.start()
    
    # Wait for result with timeout
    init_thread.join(timeout=timeout)
    
    if init_thread.is_alive():
        print(f"⏰ ChromaDB initialization timed out after {timeout}s")
        return None
    
    if not result_queue.empty():
        return result_queue.get()
    
    if not exception_queue.empty():
        raise exception_queue.get()
    
    return None

def _init_direct_chromadb_with_timeout(persist_directory, collection_name, embedding_function, timeout=10):
    """Initialize direct ChromaDB with timeout handling"""
    result_queue = queue.Queue()
    exception_queue = queue.Queue()
    
    def direct_worker():
        try:
            import chromadb
            from chromadb.config import Settings
            import uuid
            
            # Create a fresh client with unique settings
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=False,
                is_persistent=True
            )
            
            client = chromadb.PersistentClient(path=persist_directory, settings=settings)
            
            # Create wrapper to work with existing code
            class DirectChromaWrapper:
                def __init__(self, client, collection_name, embedding_fn):
                    self._client = client
                    self._embedding_function = embedding_fn
                    self.collection_name = collection_name or "default"
                    
                    # Get or create collection
                    try:
                        self._collection = client.get_collection(self.collection_name)
                        print(f"📂 Using existing collection: {self.collection_name}")
                    except:
                        self._collection = client.create_collection(
                            name=self.collection_name,
                            metadata={"hnsw:space": "cosine"}
                        )
                        print(f"🆕 Created new collection: {self.collection_name}")
                
                def similarity_search(self, query, k=4):
                    query_embedding = self._embedding_function.embed_query(query)
                    results = self._collection.query(
                        query_embeddings=[query_embedding],
                        n_results=k
                    )
                    
                    # Convert to LangChain Document format
                    try:
                        from langchain_core.documents import Document
                    except ImportError:
                        try:
                            from langchain.schema import Document
                        except ImportError:
                            # Create a simple document class if langchain not available
                            class Document:
                                def __init__(self, page_content, metadata=None):
                                    self.page_content = page_content
                                    self.metadata = metadata or {}
                    
                    documents = []
                    if results.get('documents') and results['documents'][0]:
                        for i, (doc_id, doc_text, metadata) in enumerate(zip(
                            results['ids'][0] if results.get('ids') else [], 
                            results['documents'][0] if results.get('documents') else [], 
                            results['metadatas'][0] if results.get('metadatas') else []
                        )):
                            documents.append(Document(
                                page_content=doc_text,
                                metadata=metadata or {}
                            ))
                    return documents
                
                def add_documents(self, documents):
                    texts = [doc.page_content for doc in documents]
                    metadatas = [doc.metadata for doc in documents]
                    embeddings = self._embedding_function.embed_documents(texts)
                    
                    # Generate unique IDs
                    ids = [str(uuid.uuid4()) for _ in range(len(texts))]
                    
                    self._collection.add(
                        embeddings=embeddings,
                        documents=texts,
                        metadatas=metadatas,
                        ids=ids
                    )
                
                def persist(self):
                    # ChromaDB auto-persists, so this is a no-op
                    pass
            
            wrapper = DirectChromaWrapper(client, collection_name, embedding_function)
            result_queue.put(wrapper)
            
        except Exception as e:
            exception_queue.put(e)
    
    # Start direct initialization in separate thread
    direct_thread = threading.Thread(target=direct_worker)
    direct_thread.daemon = True
    direct_thread.start()
    
    # Wait for result with timeout
    direct_thread.join(timeout=timeout)
    
    if direct_thread.is_alive():
        print(f"⏰ Direct ChromaDB initialization timed out after {timeout}s")
        return None
    
    if not result_queue.empty():
        return result_queue.get()
    
    if not exception_queue.empty():
        raise exception_queue.get()
    
    return None

def cleanup_chromadb_instances():
    """Clear all cached instances"""
    global _instances
    with _init_lock:
        for key, instance in _instances.items():
            try:
                if hasattr(instance, 'persist'):
                    instance.persist()
            except:
                pass
        _instances.clear()
        print("🧹 Cleared all ChromaDB instances")

def get_chromadb_instance(persist_directory, collection_name=None, force_new=False):
    """
    Get or create a ChromaDB instance with timeout handling
    
    Args:
        persist_directory: Path to the ChromaDB directory
        collection_name: Optional specific collection name
        force_new: Force creation of new instance
    
    Returns:
        Chroma: ChromaDB instance or None if failed
    """
    with _init_lock:
        # Create a unique key for this configuration
        key = f"{persist_directory}_{collection_name or 'default'}"
        
        # Return cached instance if exists and not forcing new
        if key in _instances and not force_new:
            return _instances[key]
        
        # If forcing new or there's a conflict, cleanup first
        if force_new or key in _instances:
            if key in _instances:
                try:
                    if hasattr(_instances[key], 'persist'):
                        _instances[key].persist()
                    del _instances[key]
                except:
                    pass
        
        # Ensure directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Get embedding function
        embedding_function = get_embedding_function()
        
        # Try initialization with timeout
        try:
            db = _init_chromadb_with_timeout(persist_directory, collection_name, embedding_function, timeout=15)
            if db is not None:
                _instances[key] = db
                
                # Check if database exists
                chroma_db_file = os.path.join(persist_directory, "chroma.sqlite3")
                if os.path.exists(chroma_db_file):
                    print(f"✅ Connected to existing ChromaDB: {chroma_db_file}")
                else:
                    print(f"🆕 Created new ChromaDB at: {persist_directory}")
                
                return db
            else:
                print("❌ ChromaDB initialization timed out")
                raise Exception("ChromaDB initialization timed out")
        
        except Exception as e:
            print(f"❌ Error initializing ChromaDB: {e}")
            
            if any(phrase in str(e).lower() for phrase in ["different settings", "already exists", "timed out"]):
                print("🔄 ChromaDB conflict detected - implementing quick cleanup...")
                
                # Clear all cached instances quickly
                cleanup_chromadb_instances()
                
                # Force garbage collection
                import gc
                gc.collect()
                
                # Quick wait
                time.sleep(0.5)
                
                print("🔄 Retrying with timeout handling...")
                try:
                    db = _init_chromadb_with_timeout(persist_directory, collection_name, embedding_function, timeout=10)
                    if db is not None:
                        _instances[key] = db
                        print("✅ Successfully resolved ChromaDB conflict with timeout handling")
                        return db
                    else:
                        print("❌ Retry timed out, falling back to direct ChromaDB")
                        raise Exception("ChromaDB retry timed out")
                    
                except Exception as e2:
                    print(f"❌ Timeout retry failed: {e2}")
                    print("🔧 Attempting final fallback to direct ChromaDB usage...")
                    
                    try:
                        wrapper = _init_direct_chromadb_with_timeout(persist_directory, collection_name, embedding_function, timeout=10)
                        if wrapper is not None:
                            _instances[key] = wrapper
                            print("✅ Successfully created direct ChromaDB wrapper with timeout")
                            return wrapper
                        else:
                            print("❌ Direct ChromaDB initialization timed out")
                    except Exception as e3:
                        print(f"❌ Direct ChromaDB fallback failed: {e3}")
            
            print("❌ All ChromaDB initialization methods failed")
            return None


def check_collection_exists(persist_directory, collection_name):
    """
    Check if a collection exists in the ChromaDB database
    
    Args:
        persist_directory: Path to the ChromaDB directory
        collection_name: Name of the collection to check
    
    Returns:
        bool: True if collection exists, False otherwise
    """
    try:
        import chromadb
        
        # Create client
        client = chromadb.PersistentClient(path=persist_directory)
        
        # Get list of collections
        collections = client.list_collections()
        collection_names = [col.name for col in collections]
        
        return collection_name in collection_names
        
    except Exception as e:
        print(f"❌ Error checking collection existence: {e}")
        return False