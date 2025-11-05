from typing import Dict, Any, List
from src.admin.chromadb_admin import ChromaDBAdmin

class DatabaseOperations:
    def __init__(self):
        self.chroma_db_admin = ChromaDBAdmin()

    def create_collection(self, collection_name: str) -> Dict[str, Any]:
        """Create a new collection in the ChromaDB."""
        return self.chroma_db_admin.create_collection(collection_name)

    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete a collection from the ChromaDB."""
        return self.chroma_db_admin.delete_collection(collection_name)

    def clear_collection(self, collection_name: str) -> Dict[str, Any]:
        """Clear all contents from a specified collection."""
        return self.chroma_db_admin.clear_collection(collection_name)

    def list_collections(self) -> List[str]:
        """List all collections in the ChromaDB."""
        return self.chroma_db_admin.list_collections()

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a specified collection."""
        return self.chroma_db_admin.get_collection_stats(collection_name)