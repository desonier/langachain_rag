#!/usr/bin/env python3

"""
Unified Database Configuration for ChromaDB Vector Database

This module provides centralized configuration for all applications
to ensure they access the same ChromaDB vector database.
"""

import os
from pathlib import Path

class VectorDBConfig:
    """Centralized configuration for vector database access"""
    
    # ===== DATABASE CONFIGURATION =====
    
    # Primary database directory - ALL applications should use this
    DB_DIRECTORY = "./resume_vectordb"
    
    # Collection name (usually handled automatically by langchain)
    COLLECTION_NAME = "langchain"
    
    # Database file name (SQLite backend)
    DB_FILE_NAME = "chroma.sqlite3"
    
    # ===== COMPUTED PATHS =====
    
    @classmethod
    def get_db_path(cls) -> str:
        """Get the absolute path to the database directory"""
        return os.path.abspath(cls.DB_DIRECTORY)
    
    @classmethod
    def get_sqlite_file_path(cls) -> str:
        """Get the absolute path to the SQLite database file"""
        return os.path.join(cls.get_db_path(), cls.DB_FILE_NAME)
    
    @classmethod
    def db_exists(cls) -> bool:
        """Check if the database SQLite file exists"""
        return os.path.exists(cls.get_sqlite_file_path())
    
    @classmethod
    def get_db_size(cls) -> int:
        """Get the size of the database file in bytes (0 if not exists)"""
        sqlite_path = cls.get_sqlite_file_path()
        return os.path.getsize(sqlite_path) if os.path.exists(sqlite_path) else 0
    
    # ===== VALIDATION METHODS =====
    
    @classmethod
    def validate_config(cls) -> dict:
        """Validate the current database configuration"""
        result = {
            'db_directory': cls.DB_DIRECTORY,
            'db_path_absolute': cls.get_db_path(),
            'sqlite_file_path': cls.get_sqlite_file_path(),
            'directory_exists': os.path.exists(cls.get_db_path()),
            'sqlite_exists': cls.db_exists(),
            'db_size_bytes': cls.get_db_size()
        }
        return result
    
    @classmethod
    def print_config_status(cls):
        """Print current database configuration status"""
        config = cls.validate_config()
        
        print("🔧 Vector Database Configuration Status")
        print("=" * 45)
        print(f"📁 Database Directory: {config['db_directory']}")
        print(f"📍 Absolute Path: {config['db_path_absolute']}")
        print(f"📄 SQLite File: {config['sqlite_file_path']}")
        print(f"📂 Directory Exists: {'✅' if config['directory_exists'] else '❌'}")
        print(f"🗃️  SQLite File Exists: {'✅' if config['sqlite_exists'] else '❌'}")
        
        if config['sqlite_exists']:
            size_mb = config['db_size_bytes'] / (1024 * 1024)
            print(f"📊 Database Size: {config['db_size_bytes']:,} bytes ({size_mb:.2f} MB)")
        
        print("=" * 45)

# ===== AZURE OPENAI CONFIGURATION =====

class AzureConfig:
    """Azure OpenAI configuration settings"""
    
    # These should be set in your .env file
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    CHATGPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
    
    @classmethod
    def validate_azure_config(cls) -> dict:
        """Validate Azure OpenAI configuration"""
        return {
            'endpoint': cls.AZURE_OPENAI_ENDPOINT is not None,
            'api_key': cls.AZURE_OPENAI_KEY is not None,
            'api_version': cls.AZURE_OPENAI_API_VERSION is not None,
            'embedding_model': cls.EMBEDDING_MODEL is not None,
            'chatgpt_deployment': cls.CHATGPT_DEPLOYMENT is not None
        }
    
    @classmethod
    def print_azure_status(cls):
        """Print Azure configuration status (without exposing secrets)"""
        config = cls.validate_azure_config()
        
        print("🔧 Azure OpenAI Configuration Status")
        print("=" * 40)
        print(f"🌐 Endpoint: {'✅' if config['endpoint'] else '❌'}")
        print(f"🔑 API Key: {'✅' if config['api_key'] else '❌'}")
        print(f"📅 API Version: {'✅' if config['api_version'] else '❌'}")
        print(f"🤖 Embedding Model: {'✅' if config['embedding_model'] else '❌'}")
        print(f"💬 ChatGPT Deployment: {'✅' if config['chatgpt_deployment'] else '❌'}")
        print("=" * 40)

# ===== CONVENIENCE FUNCTIONS =====

def get_standardized_chroma_params(embedding_function=None):
    """Get standardized parameters for ChromaDB initialization
    
    Args:
        embedding_function: The embedding function to use
        
    Returns:
        dict: Parameters for Chroma() constructor
    """
    params = {
        'persist_directory': VectorDBConfig.DB_DIRECTORY
    }
    
    if embedding_function:
        params['embedding_function'] = embedding_function
        
    return params

def print_full_config_status():
    """Print complete configuration status for debugging"""
    print("🎯 Complete System Configuration Status")
    print("=" * 50)
    print()
    
    VectorDBConfig.print_config_status()
    print()
    AzureConfig.print_azure_status()
    
    print()
    print("💡 Usage Guidelines:")
    print("   • All applications should use VectorDBConfig.DB_DIRECTORY")
    print("   • Import this module to ensure consistent paths")
    print("   • Use get_standardized_chroma_params() for Chroma initialization")

if __name__ == "__main__":
    print_full_config_status()