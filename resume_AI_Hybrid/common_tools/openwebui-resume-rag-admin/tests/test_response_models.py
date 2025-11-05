"""
Tests for response models
"""
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from datetime import datetime
from models.response_models import (
    CreateResponseModel, DeleteResponseModel, ClearResponseModel,
    ListResponseModel, StatsResponseModel, DatabaseResponseModel,
    ContentsResponseModel, CollectionInfo, CollectionStats, ContentItem
)

class TestCreateResponseModel:
    """Test CreateResponseModel"""
    
    def test_create_success_response(self):
        """Test successful create response"""
        response = CreateResponseModel(
            success=True, 
            message="Collection created successfully", 
            collection_name="test_collection",
            count=0
        )
        
        assert response.success is True
        assert response.message == "Collection created successfully"
        assert response.collection_name == "test_collection"
        assert response.count == 0
        assert response.timestamp is not None
    
    def test_create_failure_response(self):
        """Test failed create response"""
        response = CreateResponseModel(
            success=False,
            message="Collection already exists"
        )
        
        assert response.success is False
        assert response.message == "Collection already exists"
        assert response.collection_name is None
        assert response.count == 0
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        response = CreateResponseModel(
            success=True,
            message="Test message",
            collection_name="test",
            count=5
        )
        
        result = response.to_dict()
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["message"] == "Test message"
        assert result["collection_name"] == "test"
        assert result["count"] == 5
        assert "timestamp" in result

class TestDeleteResponseModel:
    """Test DeleteResponseModel"""
    
    def test_delete_success_response(self):
        """Test successful delete response"""
        response = DeleteResponseModel(
            success=True,
            message="Collection deleted",
            collection_name="test_collection",
            items_deleted=10
        )
        
        assert response.success is True
        assert response.collection_name == "test_collection"
        assert response.items_deleted == 10
    
    def test_delete_to_dict(self):
        """Test delete response to dict"""
        response = DeleteResponseModel(
            success=True,
            message="Deleted",
            collection_name="test",
            items_deleted=5
        )
        
        result = response.to_dict()
        assert result["items_deleted"] == 5

class TestClearResponseModel:
    """Test ClearResponseModel"""
    
    def test_clear_response(self):
        """Test clear collection response"""
        response = ClearResponseModel(
            success=True,
            message="Collection cleared",
            collection_name="test",
            items_cleared=15,
            final_count=0
        )
        
        assert response.success is True
        assert response.items_cleared == 15
        assert response.final_count == 0

class TestCollectionInfo:
    """Test CollectionInfo model"""
    
    def test_collection_info_with_data(self):
        """Test collection info with data"""
        info = CollectionInfo(
            name="test_collection",
            count=25,
            has_data=True,
            sample_data="Sample document text..."
        )
        
        assert info.name == "test_collection"
        assert info.count == 25
        assert info.has_data is True
        assert info.sample_data == "Sample document text..."
        assert info.error is None
    
    def test_collection_info_with_error(self):
        """Test collection info with error"""
        info = CollectionInfo(
            name="error_collection",
            count="Error",
            has_data=False,
            error="Connection failed"
        )
        
        assert info.name == "error_collection"
        assert info.count == "Error"
        assert info.has_data is False
        assert info.error == "Connection failed"
    
    def test_collection_info_to_dict(self):
        """Test collection info to dict conversion"""
        info = CollectionInfo(
            name="test",
            count=10,
            has_data=True,
            sample_data="Sample text"
        )
        
        result = info.to_dict()
        expected_keys = {"name", "count", "has_data", "sample_data"}
        assert set(result.keys()) == expected_keys

class TestListResponseModel:
    """Test ListResponseModel"""
    
    def test_list_response_with_collections(self):
        """Test list response with collections"""
        collections = [
            CollectionInfo("collection1", 10, True),
            CollectionInfo("collection2", 5, True)
        ]
        
        response = ListResponseModel(
            success=True,
            collections=collections
        )
        
        assert response.success is True
        assert response.total_collections == 2
        assert len(response.collections) == 2
    
    def test_list_response_empty(self):
        """Test list response with no collections"""
        response = ListResponseModel(success=True)
        
        assert response.success is True
        assert response.total_collections == 0
        assert len(response.collections) == 0

class TestStatsResponseModel:
    """Test StatsResponseModel"""
    
    def test_stats_response_success(self):
        """Test successful stats response"""
        collection_stats = [
            CollectionStats("collection1", 100, 66.7),
            CollectionStats("collection2", 50, 33.3)
        ]
        
        response = StatsResponseModel(
            success=True,
            database_path="/path/to/db",
            total_collections=2,
            total_items=150,
            database_size="10.5 MB",
            collections=collection_stats
        )
        
        assert response.success is True
        assert response.total_collections == 2
        assert response.total_items == 150
        assert response.database_size == "10.5 MB"
        assert len(response.collections) == 2
    
    def test_stats_response_with_error(self):
        """Test stats response with error"""
        response = StatsResponseModel(
            success=False,
            database_path="/path/to/db",
            error="Failed to connect to database"
        )
        
        assert response.success is False
        assert response.error == "Failed to connect to database"
        assert response.total_collections == 0

class TestDatabaseResponseModel:
    """Test DatabaseResponseModel"""
    
    def test_database_create_response(self):
        """Test database create response"""
        response = DatabaseResponseModel(
            success=True,
            message="Database created successfully",
            database_path="/path/to/db",
            existing_collections=0,
            operation="create"
        )
        
        assert response.success is True
        assert response.operation == "create"
        assert response.existing_collections == 0

class TestContentsResponseModel:
    """Test ContentsResponseModel"""
    
    def test_contents_response_with_data(self):
        """Test contents response with data"""
        content_items = [
            ContentItem("id1", "Document 1", {"source": "file1.txt"}),
            ContentItem("id2", "Document 2", {"source": "file2.txt"})
        ]
        
        response = ContentsResponseModel(
            success=True,
            collection_name="test_collection",
            total_count=100,
            shown_count=2,
            contents=content_items
        )
        
        assert response.success is True
        assert response.collection_name == "test_collection"
        assert response.total_count == 100
        assert response.shown_count == 2
        assert len(response.contents) == 2
    
    def test_contents_response_empty(self):
        """Test contents response with no data"""
        response = ContentsResponseModel(
            success=True,
            collection_name="empty_collection",
            total_count=0,
            shown_count=0
        )
        
        assert response.success is True
        assert response.total_count == 0
        assert response.shown_count == 0
        assert len(response.contents) == 0

class TestContentItem:
    """Test ContentItem model"""
    
    def test_content_item_full(self):
        """Test content item with all fields"""
        item = ContentItem(
            id="test_id",
            document="This is a test document",
            metadata={"source": "test.txt", "page": 1}
        )
        
        assert item.id == "test_id"
        assert item.document == "This is a test document"
        assert item.metadata["source"] == "test.txt"
        assert item.metadata["page"] == 1
    
    def test_content_item_minimal(self):
        """Test content item with minimal fields"""
        item = ContentItem(id="minimal_id")
        
        assert item.id == "minimal_id"
        assert item.document is None
        assert item.metadata == {}
    
    def test_content_item_to_dict(self):
        """Test content item to dict conversion"""
        item = ContentItem(
            id="test",
            document="Test doc",
            metadata={"key": "value"}
        )
        
        result = item.to_dict()
        expected_keys = {"id", "document", "metadata"}
        assert set(result.keys()) == expected_keys
        assert result["id"] == "test"
        assert result["document"] == "Test doc"
        assert result["metadata"]["key"] == "value"

class TestCollectionStats:
    """Test CollectionStats model"""
    
    def test_collection_stats_normal(self):
        """Test normal collection stats"""
        stats = CollectionStats(
            name="test_collection",
            count=50,
            percentage=75.0
        )
        
        assert stats.name == "test_collection"
        assert stats.count == 50
        assert stats.percentage == 75.0
        assert stats.error is None
    
    def test_collection_stats_with_error(self):
        """Test collection stats with error"""
        stats = CollectionStats(
            name="error_collection",
            count=0,
            error="Access denied"
        )
        
        assert stats.name == "error_collection"
        assert stats.count == 0
        assert stats.error == "Access denied"
    
    def test_collection_stats_to_dict(self):
        """Test collection stats to dict"""
        stats = CollectionStats("test", 25, 50.0)
        result = stats.to_dict()
        
        expected_keys = {"name", "count", "percentage"}
        assert set(result.keys()) == expected_keys