from src.admin.chromadb_admin import ChromaDBAdmin
import unittest

class TestChromaDBOperations(unittest.TestCase):
    def setUp(self):
        self.admin = ChromaDBAdmin()

    def test_create_collection(self):
        collection_name = "test_collection"
        result = self.admin.create_collection(collection_name)
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], f"✅ Collection '{collection_name}' created successfully!")

    def test_list_collections(self):
        result = self.admin.list_collections()
        self.assertTrue(result['success'])
        self.assertIsInstance(result['collections'], list)

    def test_clear_collection(self):
        collection_name = "test_collection"
        self.admin.create_collection(collection_name)  # Ensure the collection exists
        result = self.admin.clear_collection(collection_name)
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], f"✅ Collection '{collection_name}' cleared successfully!")

    def test_delete_collection(self):
        collection_name = "test_collection"
        self.admin.create_collection(collection_name)  # Ensure the collection exists
        result = self.admin.delete_collection(collection_name)
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], f"✅ Collection '{collection_name}' deleted successfully!")

    def test_get_statistics(self):
        result = self.admin.get_statistics()
        self.assertTrue(result['success'])
        self.assertIn('total_collections', result['stats'])
        self.assertIn('total_documents', result['stats'])

if __name__ == '__main__':
    unittest.main()