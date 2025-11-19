"""
ChromaDB Admin Interface with consistent settings from the main program
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings

# Import embedding function at module level to avoid import delays
try:
    import chromadb.utils.embedding_functions as embedding_functions
    EMBEDDING_FUNCTIONS_AVAILABLE = True
except ImportError:
    EMBEDDING_FUNCTIONS_AVAILABLE = False

# Add parent directories to path to import shared config
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent  # Go up to project root
sys.path.append(str(project_root))

try:
    from shared_config import get_config, get_vector_db_path
    SHARED_CONFIG_AVAILABLE = True
except ImportError:
    print("⚠️ Shared config not available, using fallback configuration")
    SHARED_CONFIG_AVAILABLE = False

class ChromaDBAdmin:
    """Admin interface for ChromaDB management with consistent settings"""
    
    def __init__(self, db_path: str = None):
        """Initialize ChromaDB Admin with consistent settings from shared config"""
        if SHARED_CONFIG_AVAILABLE:
            # Use shared configuration
            self.config = get_config()
            self.db_path = Path(db_path) if db_path else Path(get_vector_db_path())
            print(f"🔧 Using shared configuration")
            print(f"📁 Database path: {self.db_path}")
        else:
            # Fallback to hardcoded path
            self.db_path = Path(db_path) if db_path else Path("C:\\Users\\DamonDesonier\\repos\\langachain_rag\\resume_vectordb")
            print(f"📁 Using fallback database path: {self.db_path}")
        
        # Ensure directory exists
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Use consistent settings that match the main program
        self.settings = Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True
        )
        
        self.client = None
    
    def _connect(self):
        """Establish connection to ChromaDB"""
        if not self.client:
            try:
                self.client = chromadb.PersistentClient(
                    path=str(self.db_path),
                    settings=self.settings
                )
                print(f"🔌 Connected to ChromaDB at: {self.db_path}")
            except Exception as e:
                print(f"❌ Failed to connect to ChromaDB: {e}")
                raise
        return self.client
    
    def get_client(self):
        """Get or create ChromaDB client"""
        if not self.client:
            self._connect()
        return self.client
    
    def refresh_client(self):
        """Refresh the ChromaDB client connection to pick up new changes"""
        if self.client:
            try:
                # Close existing client
                del self.client
            except Exception:
                pass
        self.client = None
        # Next call to get_client() will create a fresh connection
    
    def close_client(self):
        """Properly close the ChromaDB client connection"""
        if self.client:
            try:
                print("🔌 Closing ChromaDB client connection...")
                del self.client
                self.client = None
                print("✅ ChromaDB client connection closed")
            except Exception as e:
                print(f"⚠️ Error closing ChromaDB client: {e}")
        
    def __del__(self):
        """Destructor to ensure client is closed"""
        try:
            self.close_client()
        except Exception:
            pass  # Don't raise exceptions in destructor
        
    def get_client(self):
        """Get ChromaDB client with consistent settings"""
        if self.client is None:
            try:
                self.client = chromadb.PersistentClient(
                    path=str(self.db_path),
                    settings=self.settings
                )
            except Exception as e:
                print(f"Error creating ChromaDB client: {e}")
                raise
        return self.client
    
    def create_database(self) -> Dict[str, Any]:
        """Create/Initialize the ChromaDB database"""
        try:
            client = self.get_client()
            
            # Test the connection
            collections = client.list_collections()
            
            return {
                "success": True,
                "message": f"✅ ChromaDB initialized successfully at {self.db_path}",
                "existing_collections": len(collections),
                "database_path": str(self.db_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Failed to create database: {str(e)}",
                "error": str(e)
            }
    
    def delete_database(self) -> Dict[str, Any]:
        """Delete the entire ChromaDB database"""
        try:
            # Close client connection
            if self.client:
                del self.client
                self.client = None
            
            # Remove database files
            import shutil
            if self.db_path.exists():
                shutil.rmtree(self.db_path)
                
            return {
                "success": True,
                "message": f"✅ Database deleted successfully from {self.db_path}",
                "database_path": str(self.db_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Failed to delete database: {str(e)}",
                "error": str(e)
            }
    
    def create_collection(self, collection_name: str) -> Dict[str, Any]:
        """Create a new collection with the correct embedding function"""
        try:
            client = self.get_client()
            
            # Check if collection already exists
            try:
                existing = client.get_collection(collection_name)
                return {
                    "success": False,
                    "message": f"❌ Collection '{collection_name}' already exists",
                    "collection_name": collection_name
                }
            except:
                pass  # Collection doesn't exist, which is what we want
            
            # Create embedding function only if available, otherwise use default
            embedding_function = None
            if EMBEDDING_FUNCTIONS_AVAILABLE:
                try:
                    # Create HuggingFace embedding function to match the shared config
                    # This ensures all collections use the same embedding model
                    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name="sentence-transformers/all-MiniLM-L6-v2",
                        device="cpu",
                        normalize_embeddings=True
                    )
                    print(f"✅ Using sentence-transformers/all-MiniLM-L6-v2 embedding function for collection '{collection_name}'")
                except Exception as e:
                    print(f"⚠️ Warning: Could not create custom embedding function: {e}")
                    print("📝 Using default ChromaDB embedding function")
                    embedding_function = None
            
            # Create the collection with or without custom embedding function
            if embedding_function:
                collection = client.create_collection(
                    name=collection_name,
                    embedding_function=embedding_function
                )
                message = f"✅ Collection '{collection_name}' created successfully with sentence-transformers/all-MiniLM-L6-v2 embeddings"
            else:
                collection = client.create_collection(name=collection_name)
                message = f"✅ Collection '{collection_name}' created successfully with default embeddings"
            
            return {
                "success": True,
                "message": message,
                "collection_name": collection_name,
                "count": 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Failed to create collection '{collection_name}': {str(e)}",
                "error": str(e)
            }
    
    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete a collection"""
        try:
            client = self.get_client()
            
            # Check if collection exists
            try:
                collection = client.get_collection(collection_name)
                count = collection.count()
            except:
                return {
                    "success": False,
                    "message": f"❌ Collection '{collection_name}' does not exist",
                    "collection_name": collection_name
                }
            
            # Delete the collection
            client.delete_collection(collection_name)
            
            return {
                "success": True,
                "message": f"✅ Collection '{collection_name}' deleted successfully (had {count} items)",
                "collection_name": collection_name,
                "items_deleted": count
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Failed to delete collection '{collection_name}': {str(e)}",
                "error": str(e)
            }
    
    def clear_collection(self, collection_name: str) -> Dict[str, Any]:
        """Clear all contents from a collection"""
        try:
            client = self.get_client()
            
            # Get the collection
            try:
                collection = client.get_collection(collection_name)
                count_before = collection.count()
            except:
                return {
                    "success": False,
                    "message": f"❌ Collection '{collection_name}' does not exist",
                    "collection_name": collection_name
                }
            
            if count_before == 0:
                return {
                    "success": True,
                    "message": f"✅ Collection '{collection_name}' is already empty",
                    "collection_name": collection_name,
                    "items_cleared": 0
                }
            
            # Get all IDs and delete them
            results = collection.get()
            if results['ids']:
                collection.delete(ids=results['ids'])
            
            count_after = collection.count()
            
            return {
                "success": True,
                "message": f"✅ Collection '{collection_name}' cleared successfully ({count_before} items removed)",
                "collection_name": collection_name,
                "items_cleared": count_before,
                "final_count": count_after
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Failed to clear collection '{collection_name}': {str(e)}",
                "error": str(e)
            }
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections with their stats"""
        try:
            client = self.get_client()
            collections = client.list_collections()
            
            collection_list = []
            for collection in collections:
                try:
                    count = collection.count()  # Total chunks
                    
                    # Count unique documents in this collection
                    unique_documents = 0
                    try:
                        all_results = collection.get(include=["metadatas"])
                        if all_results and all_results.get("metadatas"):
                            unique_sources = set()
                            for metadata in all_results["metadatas"]:
                                if metadata:
                                    source = metadata.get("original_file_source") or metadata.get("source")
                                    if source:
                                        unique_sources.add(source)
                            unique_documents = len(unique_sources)
                    except Exception as e:
                        print(f"⚠️ Error counting unique documents for {collection.name}: {e}")
                    
                    # Create collection summary instead of showing raw data
                    summary_data = None
                    if unique_documents > 0:
                        summary_data = f"📊 {unique_documents} document{'s' if unique_documents != 1 else ''} ({count} chunks)"
                    else:
                        summary_data = "Empty collection"
                    
                    collection_list.append({
                        "name": collection.name,
                        "count": unique_documents,  # Show document count instead of chunk count
                        "chunk_count": count,  # Keep chunk count for reference
                        "sample_data": summary_data,
                        "has_data": unique_documents > 0
                    })
                except Exception as e:
                    collection_list.append({
                        "name": collection.name,
                        "count": "Error",
                        "error": str(e),
                        "has_data": False
                    })
            
            return collection_list
            
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []
    
    def get_collection_contents(self, collection_name: str, limit: int = 10) -> Dict[str, Any]:
        """Get contents of a specific collection"""
        try:
            client = self.get_client()
            
            try:
                collection = client.get_collection(collection_name)
            except:
                return {
                    "success": False,
                    "message": f"❌ Collection '{collection_name}' does not exist"
                }
            
            # Get collection data
            results = collection.get(limit=limit)
            
            # Count unique documents in this collection
            total_documents = 0
            try:
                all_results = collection.get(include=["metadatas"])
                if all_results and all_results.get("metadatas"):
                    unique_sources = set()
                    for metadata in all_results["metadatas"]:
                        if metadata:
                            source = metadata.get("original_file_source") or metadata.get("source")
                            if source:
                                unique_sources.add(source)
                    total_documents = len(unique_sources)
            except Exception as e:
                print(f"⚠️ Error counting unique documents: {e}")
            
            contents = []
            for i, doc_id in enumerate(results['ids']):
                content_item = {
                    "id": doc_id,
                    "document": results['documents'][i] if i < len(results['documents']) else None,
                    "metadata": results['metadatas'][i] if i < len(results['metadatas']) else {}
                }
                contents.append(content_item)
            
            return {
                "success": True,
                "collection_name": collection_name,
                "total_count": collection.count(),  # Total chunks
                "total_documents": total_documents,  # Unique documents
                "shown_count": len(contents),
                "contents": contents
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Failed to get contents of '{collection_name}': {str(e)}",
                "error": str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            # Refresh client to ensure we get latest data
            self.refresh_client()
            client = self.get_client()
            collections = client.list_collections()
            
            total_items = 0
            total_documents = 0  # Count unique documents/resumes
            collection_stats = []
            
            for collection in collections:
                try:
                    count = collection.count()
                    total_items += count
                    
                    # Count unique documents by getting unique source files
                    unique_docs = 0
                    try:
                        # Get all items with metadata - using no limit to ensure we get all
                        results = collection.get(include=["metadatas"])
                        
                        if results and results.get("metadatas"):
                            # Extract unique source files
                            unique_sources = set()
                            for metadata in results["metadatas"]:
                                if metadata:
                                    # Check for original_file_source first, then fallback to source
                                    source = metadata.get("original_file_source") or metadata.get("source")
                                    if source:
                                        unique_sources.add(source)
                            unique_docs = len(unique_sources)
                            total_documents += unique_docs
                    except Exception as doc_count_error:
                        print(f"⚠️ Error counting unique documents for {collection.name}: {doc_count_error}")
                        unique_docs = "Error"
                    
                    collection_stats.append({
                        "name": collection.name,
                        "count": count,  # Total chunks
                        "documents": unique_docs,  # Unique documents/resumes
                        "percentage": 0  # Will calculate after getting total
                    })
                except Exception as e:
                    collection_stats.append({
                        "name": collection.name,
                        "count": "Error",
                        "documents": "Error",
                        "error": str(e)
                    })
            
            # Calculate percentages based on document count
            for stat in collection_stats:
                if isinstance(stat["documents"], int) and total_documents > 0:
                    stat["percentage"] = round((stat["documents"] / total_documents) * 100, 1)
            
            # Get database size
            db_size = "Unknown"
            try:
                db_file = self.db_path / "chroma.sqlite3"
                if db_file.exists():
                    size_bytes = db_file.stat().st_size
                    db_size = f"{size_bytes / (1024 * 1024):.2f} MB"
            except Exception as e:
                db_size = f"Error: {e}"
            
            return {
                "database_path": str(self.db_path),
                "total_collections": len(collections),
                "total_items": total_items,  # Total chunks
                "total_documents": total_documents,  # Unique documents/resumes
                "database_size": db_size,
                "collections": collection_stats,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get statistics: {str(e)}",
                "database_path": str(self.db_path),
                "last_updated": datetime.now().isoformat()
            }
    
    def clear_all_collections(self) -> Dict[str, Any]:
        """Clear all documents from all collections"""
        try:
            client = self.get_client()
            collections = client.list_collections()
            
            if not collections:
                return {
                    "success": True,
                    "message": "✅ No collections found to clear",
                    "collections_cleared": 0,
                    "total_items_removed": 0
                }
            
            total_items_removed = 0
            collections_cleared = 0
            
            for collection in collections:
                try:
                    # Get collection and count items
                    coll = client.get_collection(collection.name)
                    count_before = coll.count()
                    
                    if count_before > 0:
                        # Get all document IDs and delete them
                        results = coll.get(include=[])  # Get only IDs
                        if results['ids']:
                            coll.delete(ids=results['ids'])
                            total_items_removed += count_before
                            collections_cleared += 1
                            
                except Exception as e:
                    print(f"⚠️ Warning: Failed to clear collection {collection.name}: {e}")
                    continue
            
            return {
                "success": True,
                "message": f"✅ Cleared {collections_cleared} collections, removed {total_items_removed} items",
                "collections_cleared": collections_cleared,
                "total_items_removed": total_items_removed
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Failed to clear all collections: {str(e)}",
                "error": str(e)
            }
    
    def reset_database(self) -> Dict[str, Any]:
        """Reset the entire database by deleting all collections"""
        try:
            client = self.get_client()
            collections = client.list_collections()
            
            if not collections:
                return {
                    "success": True,
                    "message": "✅ Database is already empty",
                    "collections_deleted": 0
                }
            
            collections_deleted = 0
            total_items_removed = 0
            
            for collection in collections:
                try:
                    # Get count before deletion
                    coll = client.get_collection(collection.name)
                    count = coll.count()
                    
                    # Delete the collection
                    client.delete_collection(collection.name)
                    collections_deleted += 1
                    total_items_removed += count
                    
                except Exception as e:
                    print(f"⚠️ Warning: Failed to delete collection {collection.name}: {e}")
                    continue
            
            return {
                "success": True,
                "message": f"✅ Database reset: deleted {collections_deleted} collections with {total_items_removed} items",
                "collections_deleted": collections_deleted,
                "total_items_removed": total_items_removed
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Failed to reset database: {str(e)}",
                "error": str(e)
            }
    
    def get_database_health(self) -> Dict[str, Any]:
        """Check database health and connectivity"""
        try:
            client = self.get_client()
            collections = client.list_collections()
            
            # Test basic operations
            health_checks = {
                "client_connection": True,
                "collections_accessible": True,
                "database_readable": True,
                "database_writable": False
            }
            
            # Test write capabilities with a temporary collection
            try:
                test_collection_name = "_health_check_temp"
                
                # Clean up any existing test collection
                try:
                    client.delete_collection(test_collection_name)
                except:
                    pass
                
                # Create test collection
                test_collection = client.create_collection(test_collection_name)
                
                # Test write
                test_collection.add(
                    documents=["health check test"],
                    ids=["health_test_1"],
                    metadatas=[{"test": True}]
                )
                
                # Test read
                result = test_collection.get(ids=["health_test_1"])
                if result['ids']:
                    health_checks["database_writable"] = True
                
                # Clean up test collection
                client.delete_collection(test_collection_name)
                
            except Exception as e:
                print(f"⚠️ Write test failed: {e}")
            
            # Calculate overall health score
            health_score = sum(health_checks.values()) / len(health_checks) * 100
            
            return {
                "success": True,
                "healthy": health_score >= 75,
                "health_score": health_score,
                "checks": health_checks,
                "collections_count": len(collections),
                "database_path": str(self.db_path),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "healthy": False,
                "health_score": 0,
                "error": str(e),
                "database_path": str(self.db_path),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_existing_db_connection(self):
        """Get the existing database connection for reuse in pipelines"""
        try:
            if not self.client:
                self._connect()
            
            # Return a simplified interface that can be used by the pipeline
            return {
                'client': self.client,
                'db_path': str(self.db_path),
                'settings': self.settings
            }
        except Exception as e:
            print(f"⚠️ Could not get existing DB connection: {e}")
            return None
    
    def health_check(self):
        """
        Perform a comprehensive health check of the ChromaDB connection
        Returns: dict with health status and details
        """
        try:
            # Ensure we have a connection
            if not self.client:
                self._connect()
            
            # Test basic operations
            health_status = {
                'healthy': True,
                'checks': {},
                'error': None,
                'timestamp': datetime.now().isoformat()
            }
            
            # Check 1: List collections
            try:
                collections = self.client.list_collections()
                health_status['checks']['list_collections'] = {
                    'status': 'pass',
                    'count': len(collections),
                    'message': f"Found {len(collections)} collections"
                }
            except Exception as e:
                health_status['healthy'] = False
                health_status['checks']['list_collections'] = {
                    'status': 'fail',
                    'error': str(e),
                    'message': "Failed to list collections"
                }
            
            # Check 2: Database path accessibility
            try:
                if self.db_path.exists():
                    health_status['checks']['database_path'] = {
                        'status': 'pass',
                        'path': str(self.db_path),
                        'message': "Database path accessible"
                    }
                else:
                    health_status['healthy'] = False
                    health_status['checks']['database_path'] = {
                        'status': 'fail',
                        'path': str(self.db_path),
                        'message': "Database path does not exist"
                    }
            except Exception as e:
                health_status['healthy'] = False
                health_status['checks']['database_path'] = {
                    'status': 'fail',
                    'error': str(e),
                    'message': "Database path check failed"
                }
            
            # Check 3: Test creating/getting a health check collection
            try:
                test_collection_name = "__health_check__"
                try:
                    # Try to get existing health check collection
                    test_collection = self.client.get_collection(test_collection_name)
                    health_status['checks']['test_collection'] = {
                        'status': 'pass',
                        'message': "Test collection accessible"
                    }
                except:
                    # Create temporary test collection
                    test_collection = self.client.create_collection(
                        name=test_collection_name,
                        metadata={"temp": True}
                    )
                    health_status['checks']['test_collection'] = {
                        'status': 'pass',
                        'message': "Test collection created successfully"
                    }
                
                # Clean up test collection
                try:
                    self.client.delete_collection(test_collection_name)
                except:
                    pass  # Don't fail health check if cleanup fails
                    
            except Exception as e:
                health_status['healthy'] = False
                health_status['checks']['test_collection'] = {
                    'status': 'fail',
                    'error': str(e),
                    'message': "Failed to create/access test collection"
                }
            
            # Set overall error message if unhealthy
            if not health_status['healthy']:
                failed_checks = [check for check, details in health_status['checks'].items() 
                               if details['status'] == 'fail']
                health_status['error'] = f"Health check failed: {', '.join(failed_checks)}"
            
            return health_status
            
        except Exception as e:
            return {
                'healthy': False,
                'error': f"Health check exception: {str(e)}",
                'checks': {},
                'timestamp': datetime.now().isoformat()
            }