from pathlib import Path
import os

class DatabaseConfig:
    """Configuration settings for connecting to the ChromaDB database."""

    def __init__(self):
        self.db_path = self.get_db_path()
        self.collection_name = "resumes"  # Default collection name

    def get_db_path(self) -> str:
        """Get the database path from environment variables or use a default."""
        return os.getenv("CHROMADB_PATH", str(Path.home() / "chroma_db" / "chroma.sqlite3"))

    def get_collection_name(self) -> str:
        """Get the collection name."""
        return self.collection_name

    def set_collection_name(self, name: str):
        """Set the collection name."""
        self.collection_name = name

    def display_config(self) -> dict:
        """Display the current database configuration."""
        return {
            "Database Path": self.db_path,
            "Collection Name": self.collection_name
        }