from src.admin.chromadb_admin import ChromaDBAdmin
import unittest

class TestChromaDBAdmin(unittest.TestCase):
    def setUp(self):
        self.admin = ChromaDBAdmin()

    def test_create_collection(self):
        response = self.admin.create_collection("test_collection")
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], "✅ Collection 'test_collection' created successfully!")

    def test_list_collections(self):
        self.admin.create_collection("test_collection")
        collections = self.admin.list_collections()
        self.assertIn("test_collection", collections)

    def test_clear_collection(self):
        self.admin.create_collection("test_collection")
        response = self.admin.clear_collection("test_collection")
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], "✅ Collection 'test_collection' cleared successfully!")

    def test_delete_collection(self):
        self.admin.create_collection("test_collection")
        response = self.admin.delete_collection("test_collection")
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], "✅ Collection 'test_collection' deleted successfully!")

    def test_get_statistics(self):
        self.admin.create_collection("test_collection")
        stats = self.admin.get_statistics("test_collection")
        self.assertIn("total_items", stats)
        self.assertIn("collection_name", stats)

if __name__ == '__main__':
    unittest.main()