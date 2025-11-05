from typing import Dict, Any, List
from chromadb_admin import ChromaDBAdmin

class CollectionManager:
    """Manages collections within the ChromaDB."""

    def __init__(self):
        self.chroma_db_admin = ChromaDBAdmin()

    def create_collection(self, collection_name: str) -> Dict[str, Any]:
        """Create a new collection in the ChromaDB."""
        result = self.chroma_db_admin.create_collection(collection_name)
        return result

    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete a collection from the ChromaDB."""
        result = self.chroma_db_admin.delete_collection(collection_name)
        return result

    def clear_collection(self, collection_name: str) -> Dict[str, Any]:
        """Clear all contents from a collection in the ChromaDB."""
        result = self.chroma_db_admin.clear_collection(collection_name)
        return result

    def list_collections(self) -> List[str]:
        """List all collections in the ChromaDB."""
        collections = self.chroma_db_admin.list_collections()
        return collections

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a specific collection in the ChromaDB."""
        stats = self.chroma_db_admin.get_collection_stats(collection_name)
        return stats