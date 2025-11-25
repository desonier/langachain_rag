"""
Shared Configuration for Resume RAG System
Ensures all interfaces (Streamlit, OpenWebUI, etc.) use the same database and settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SharedConfig:
    """Centralized configuration for Resume RAG System"""
    
    def __init__(self):
        # Set up base paths
        self.project_root = Path(__file__).parent.absolute()
        self.data_directory = self.project_root / "data"
        
        # Vector Database Configuration
        self.vector_db_path = self._get_vector_db_path()
        self.collection_name = "resumes"
        
        # Azure OpenAI Configuration
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self.azure_openai_deployment = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        # Embedding Configuration
        self.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "huggingface")  # huggingface, azure-openai, openai
        self.embedding_model = self._get_embedding_model()
        self.embedding_device = "cpu"
        self.normalize_embeddings = True
        
        # LLM Configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "azure-openai")  # azure-openai, openai, anthropic
        self.llm_model = self._get_llm_model()
        self.llm_temperature = 0.1
        self.disable_search_enhancement = True
        
        # File Processing Configuration
        self.supported_formats = ['.pdf', '.docx']
        self.chunk_size = 500
        self.chunk_overlap = 50
        self.max_chunks_per_query = 4
        
        # Validate configuration
        self._validate_config()
    
    def _get_vector_db_path(self):
        """Get the vector database path (prioritize environment variable, then default)"""
        # Check environment variable first
        env_db_path = os.getenv("VECTOR_DB_PATH")
        if env_db_path:
            return Path(env_db_path).absolute()
        
        # Check if we're in the main project directory
        potential_paths = [
            self.project_root / "resume_vectordb",  # Project root
            Path("C:/Users/DamonDesonier/repos/langachain_rag/resume_vectordb"),  # Absolute path from your setup
            self.project_root.parent / "resume_vectordb",  # Parent directory
        ]
        
        # Use existing database if found
        for path in potential_paths:
            if path.exists() and (path / "chroma.sqlite3").exists():
                print(f"✅ Found existing database at: {path}")
                return path.absolute()
        
        # Default to project root if none found
        default_path = self.project_root / "resume_vectordb"
        print(f"📁 Using default database path: {default_path}")
        return default_path.absolute()
    
    def _get_embedding_model(self):
        """Get embedding model based on provider"""
        provider = self.embedding_provider.lower()
        
        if provider == "huggingface":
            return os.getenv("HUGGINGFACE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        elif provider == "azure-openai":
            return os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        elif provider == "openai":
            return os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
        else:
            return "sentence-transformers/all-MiniLM-L6-v2"  # fallback
    
    def _get_llm_model(self):
        """Get LLM model based on provider"""
        provider = self.llm_provider.lower()
        
        if provider == "azure-openai":
            return self.azure_openai_deployment or "gpt-4"
        elif provider == "openai":
            return os.getenv("OPENAI_MODEL", "gpt-4")
        elif provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        else:
            return self.azure_openai_deployment or "gpt-4"  # fallback
    
    def get_available_embedding_providers(self):
        """Get list of available embedding providers"""
        return [
            {"id": "huggingface", "name": "HuggingFace Transformers", "models": [
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2",
                "sentence-transformers/paraphrase-MiniLM-L6-v2"
            ]},
            {"id": "azure-openai", "name": "Azure OpenAI", "models": [
                "text-embedding-ada-002",
                "text-embedding-3-small",
                "text-embedding-3-large"
            ]},
            {"id": "openai", "name": "OpenAI", "models": [
                "text-embedding-ada-002",
                "text-embedding-3-small", 
                "text-embedding-3-large"
            ]}
        ]
    
    def get_available_llm_providers(self):
        """Get list of available LLM providers"""
        return [
            {"id": "azure-openai", "name": "Azure OpenAI", "models": [
                "gpt-4",
                "gpt-4-turbo",
                "gpt-35-turbo",
                "gpt-4o"
            ]},
            {"id": "openai", "name": "OpenAI", "models": [
                "gpt-4",
                "gpt-4-turbo-preview",
                "gpt-3.5-turbo",
                "gpt-4o"
            ]},
            {"id": "anthropic", "name": "Anthropic", "models": [
                "claude-3-sonnet-20240229",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ]}
        ]
    
    def _validate_config(self):
        """Validate required configuration"""
        self.validation_errors = []
        
        # Check Azure OpenAI configuration
        if not self.azure_openai_endpoint:
            self.validation_errors.append("AZURE_OPENAI_ENDPOINT not set")
        
        if not self.azure_openai_key:
            self.validation_errors.append("AZURE_OPENAI_KEY not set")
        
        if not self.azure_openai_deployment:
            self.validation_errors.append("AZURE_OPENAI_CHATGPT_DEPLOYMENT not set")
        
        # Ensure data directory exists
        self.data_directory.mkdir(exist_ok=True)
    
    def is_valid(self):
        """Check if configuration is valid"""
        return len(self.validation_errors) == 0
    
    def get_validation_errors(self):
        """Get list of validation errors"""
        return self.validation_errors
    
    def get_database_info(self):
        """Get database information"""
        chroma_file = self.vector_db_path / "chroma.sqlite3"
        return {
            "path": str(self.vector_db_path),
            "exists": self.vector_db_path.exists(),
            "chroma_file_exists": chroma_file.exists(),
            "collection_name": self.collection_name,
            "size_mb": round(chroma_file.stat().st_size / (1024 * 1024), 2) if chroma_file.exists() else 0
        }
    
    def get_azure_config(self):
        """Get Azure OpenAI configuration"""
        return {
            "endpoint": self.azure_openai_endpoint,
            "api_version": self.azure_openai_api_version,
            "deployment": self.azure_openai_deployment,
            "has_key": bool(self.azure_openai_key),
            "temperature": self.llm_temperature
        }
    
    def get_embedding_config(self):
        """Get embedding configuration"""
        return {
            "model": self.embedding_model,
            "device": self.embedding_device,
            "normalize": self.normalize_embeddings
        }
    
    def print_config_summary(self):
        """Print configuration summary"""
        print("🔧 Resume RAG System Configuration")
        print("=" * 50)
        
        # Database info
        db_info = self.get_database_info()
        print(f"📁 Vector Database:")
        print(f"   Path: {db_info['path']}")
        print(f"   Exists: {'✅' if db_info['exists'] else '❌'}")
        print(f"   ChromaDB File: {'✅' if db_info['chroma_file_exists'] else '❌'}")
        if db_info['size_mb'] > 0:
            print(f"   Size: {db_info['size_mb']} MB")
        
        # Azure config
        azure_config = self.get_azure_config()
        print(f"\n🔑 Azure OpenAI:")
        print(f"   Endpoint: {'✅' if azure_config['endpoint'] else '❌'}")
        print(f"   API Key: {'✅' if azure_config['has_key'] else '❌'}")
        print(f"   Deployment: {azure_config['deployment'] or '❌ Not set'}")
        print(f"   API Version: {azure_config['api_version']}")
        
        # Model configuration
        print(f"\n🤖 Model Configuration:")
        print(f"   LLM Provider: {self.llm_provider}")
        print(f"   LLM Model: {self.llm_model}")
        print(f"   Embedding Provider: {self.embedding_provider}")
        print(f"   Embedding Model: {self.embedding_model}")
        print(f"   Temperature: {self.llm_temperature}")
        
        # Validation
        print(f"\n✅ Configuration Status: {'Valid' if self.is_valid() else 'Invalid'}")
        if not self.is_valid():
            print("❌ Validation Errors:")
            for error in self.validation_errors:
                print(f"   - {error}")
        
        print("=" * 50)

# Global configuration instance
config = SharedConfig()

def get_config():
    """Get the global configuration instance"""
    return config

def get_vector_db_path():
    """Get the vector database path as string"""
    return str(config.vector_db_path)

def get_azure_llm_config():
    """Get Azure LLM configuration for direct use"""
    return {
        "azure_endpoint": config.azure_openai_endpoint,
        "api_key": config.azure_openai_key,
        "api_version": config.azure_openai_api_version,
        "azure_deployment": config.azure_openai_deployment,  # Fixed: was 'deployment_name', should be 'azure_deployment'
        "temperature": config.llm_temperature,
        "model_kwargs": {
            "extra_headers": {
                "ms-azure-ai-chat-enhancements-disable-search": "true"
            }
        } if config.disable_search_enhancement else {}
    }

def get_embedding_config():
    """Get embedding configuration for direct use"""
    return {
        "model_name": config.embedding_model,
        "model_kwargs": {"device": config.embedding_device},
        "encode_kwargs": {"normalize_embeddings": config.normalize_embeddings}
    }

def get_dynamic_llm_config(provider=None, model=None):
    """Get LLM configuration for specified provider and model"""
    provider = provider or config.llm_provider
    model = model or config.llm_model
    
    if provider == "azure-openai":
        return {
            "azure_endpoint": config.azure_openai_endpoint,
            "api_key": config.azure_openai_key,
            "api_version": config.azure_openai_api_version,
            "azure_deployment": model,  # Fixed: was 'deployment_name', should be 'azure_deployment'
            "temperature": config.llm_temperature,
            "model_kwargs": {
                "extra_headers": {
                    "ms-azure-ai-chat-enhancements-disable-search": "true"
                }
            } if config.disable_search_enhancement else {}
        }
    elif provider == "openai":
        return {
            "model": model,
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": config.llm_temperature
        }
    elif provider == "anthropic":
        return {
            "model": model,
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "temperature": config.llm_temperature
        }
    else:
        return get_azure_llm_config()  # fallback

def get_dynamic_embedding_config(provider=None, model=None):
    """Get embedding configuration for specified provider and model"""
    provider = provider or config.embedding_provider
    model = model or config.embedding_model
    
    if provider == "huggingface":
        return {
            "model_name": model,
            "model_kwargs": {"device": config.embedding_device},
            "encode_kwargs": {"normalize_embeddings": config.normalize_embeddings}
        }
    elif provider == "azure-openai":
        return {
            "azure_endpoint": config.azure_openai_endpoint,
            "api_key": config.azure_openai_key,
            "api_version": config.azure_openai_api_version,
            "model": model
        }
    elif provider == "openai":
        return {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": model
        }
    else:
        return get_embedding_config()  # fallback

if __name__ == "__main__":
    # Print configuration when run directly
    config.print_config_summary()