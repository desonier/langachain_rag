"""
Pytest configuration and fixtures for ChromaDB Admin tests
"""
import sys
import os
from pathlib import Path

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Set up environment variables for testing
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("TESTING", "true")

import pytest

@pytest.fixture
def app_config():
    """Test application configuration"""
    return {
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False
    }

@pytest.fixture
def sample_collection_data():
    """Sample collection data for testing"""
    return {
        "name": "test_collection",
        "count": 25,
        "has_data": True,
        "sample_data": "This is sample document content for testing..."
    }

@pytest.fixture
def sample_database_stats():
    """Sample database statistics for testing"""
    return {
        "database_path": "/test/path/to/db",
        "total_collections": 3,
        "total_items": 150,
        "database_size": "12.5 MB",
        "last_updated": "2024-01-15T10:30:00"
    }