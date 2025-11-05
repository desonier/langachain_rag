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
        """Create a new collection"""
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
            
            # Create the collection
            collection = client.create_collection(collection_name)
            
            return {
                "success": True,
                "message": f"✅ Collection '{collection_name}' created successfully",
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
                    count = collection.count()
                    
                    # Get sample data if available
                    sample_data = None
                    if count > 0:
                        sample = collection.peek(limit=1)
                        if sample['documents']:
                            sample_data = sample['documents'][0][:100] + "..." if len(sample['documents'][0]) > 100 else sample['documents'][0]
                    
                    collection_list.append({
                        "name": collection.name,
                        "count": count,
                        "sample_data": sample_data,
                        "has_data": count > 0
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
                "total_count": collection.count(),
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
            client = self.get_client()
            collections = client.list_collections()
            
            total_items = 0
            collection_stats = []
            
            for collection in collections:
                try:
                    count = collection.count()
                    total_items += count
                    
                    collection_stats.append({
                        "name": collection.name,
                        "count": count,
                        "percentage": 0  # Will calculate after getting total
                    })
                except Exception as e:
                    collection_stats.append({
                        "name": collection.name,
                        "count": "Error",
                        "error": str(e)
                    })
            
            # Calculate percentages
            for stat in collection_stats:
                if isinstance(stat["count"], int) and total_items > 0:
                    stat["percentage"] = round((stat["count"] / total_items) * 100, 1)
            
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
                "total_items": total_items,
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