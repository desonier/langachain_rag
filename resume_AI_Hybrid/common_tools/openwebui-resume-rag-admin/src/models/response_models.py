from typing import Dict, Any, List, Optional
from datetime import datetime

class CreateResponseModel:
    """Response model for creating a new collection in ChromaDB."""
    def __init__(self, success: bool, message: str, collection_name: str = None, count: int = 0):
        self.success = success
        self.message = message
        self.collection_name = collection_name
        self.count = count
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "collection_name": self.collection_name,
            "count": self.count,
            "timestamp": self.timestamp
        }

class DeleteResponseModel:
    """Response model for deleting a collection in ChromaDB."""
    def __init__(self, success: bool, message: str, collection_name: str = None, items_deleted: int = 0):
        self.success = success
        self.message = message
        self.collection_name = collection_name
        self.items_deleted = items_deleted
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "collection_name": self.collection_name,
            "items_deleted": self.items_deleted,
            "timestamp": self.timestamp
        }

class ClearResponseModel:
    """Response model for clearing contents of a collection in ChromaDB."""
    def __init__(self, success: bool, message: str, collection_name: str = None, items_cleared: int = 0, final_count: int = 0):
        self.success = success
        self.message = message
        self.collection_name = collection_name
        self.items_cleared = items_cleared
        self.final_count = final_count
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "collection_name": self.collection_name,
            "items_cleared": self.items_cleared,
            "final_count": self.final_count,
            "timestamp": self.timestamp
        }

class CollectionInfo:
    """Model for collection information."""
    def __init__(self, name: str, count: int, has_data: bool = False, sample_data: str = None, error: str = None):
        self.name = name
        self.count = count
        self.has_data = has_data
        self.sample_data = sample_data
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "count": self.count,
            "has_data": self.has_data
        }
        if self.sample_data:
            data["sample_data"] = self.sample_data
        if self.error:
            data["error"] = self.error
        return data

class ListResponseModel:
    """Response model for listing collections in ChromaDB."""
    def __init__(self, success: bool, message: str = None, collections: List[CollectionInfo] = None):
        self.success = success
        self.message = message or ("Collections retrieved successfully" if success else "Failed to retrieve collections")
        self.collections = collections or []
        self.total_collections = len(self.collections)
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "total_collections": self.total_collections,
            "collections": [col.to_dict() for col in self.collections],
            "timestamp": self.timestamp
        }

class CollectionStats:
    """Model for collection statistics."""
    def __init__(self, name: str, count: int, percentage: float = 0.0, error: str = None):
        self.name = name
        self.count = count
        self.percentage = percentage
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "count": self.count,
            "percentage": self.percentage
        }
        if self.error:
            data["error"] = self.error
        return data

class StatsResponseModel:
    """Response model for database statistics."""
    def __init__(self, success: bool, database_path: str, total_collections: int = 0, 
                 total_items: int = 0, database_size: str = "Unknown", 
                 collections: List[CollectionStats] = None, error: str = None):
        self.success = success
        self.database_path = database_path
        self.total_collections = total_collections
        self.total_items = total_items
        self.database_size = database_size
        self.collections = collections or []
        self.error = error
        self.last_updated = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "success": self.success,
            "database_path": self.database_path,
            "total_collections": self.total_collections,
            "total_items": self.total_items,
            "database_size": self.database_size,
            "collections": [col.to_dict() for col in self.collections],
            "last_updated": self.last_updated
        }
        if self.error:
            data["error"] = self.error
        return data

class DatabaseResponseModel:
    """Response model for database operations (create/delete)."""
    def __init__(self, success: bool, message: str, database_path: str = None, 
                 existing_collections: int = 0, operation: str = None):
        self.success = success
        self.message = message
        self.database_path = database_path
        self.existing_collections = existing_collections
        self.operation = operation
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "database_path": self.database_path,
            "existing_collections": self.existing_collections,
            "operation": self.operation,
            "timestamp": self.timestamp
        }

class ContentItem:
    """Model for individual collection content item."""
    def __init__(self, id: str, document: str = None, metadata: Dict[str, Any] = None):
        self.id = id
        self.document = document
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document": self.document,
            "metadata": self.metadata
        }

class ContentsResponseModel:
    """Response model for collection contents."""
    def __init__(self, success: bool, collection_name: str = None, total_count: int = 0,
                 shown_count: int = 0, contents: List[ContentItem] = None, message: str = None):
        self.success = success
        self.collection_name = collection_name
        self.total_count = total_count
        self.shown_count = shown_count
        self.contents = contents or []
        self.message = message or ("Contents retrieved successfully" if success else "Failed to retrieve contents")
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "collection_name": self.collection_name,
            "total_count": self.total_count,
            "shown_count": self.shown_count,
            "contents": [item.to_dict() for item in self.contents],
            "message": self.message,
            "timestamp": self.timestamp
        }