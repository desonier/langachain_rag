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
        response = self.admin.list_collections()
        self.assertTrue(response['success'])
        self.assertIn("test_collection", response['collections'])

    def test_clear_collection(self):
        response = self.admin.clear_collection("test_collection")
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], "✅ Collection 'test_collection' cleared successfully!")

    def test_delete_collection(self):
        response = self.admin.delete_collection("test_collection")
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], "✅ Collection 'test_collection' deleted successfully!")

    def test_display_statistics(self):
        response = self.admin.display_statistics()
        self.assertTrue(response['success'])
        self.assertIn("total_collections", response['stats'])

if __name__ == '__main__':
    unittest.main()