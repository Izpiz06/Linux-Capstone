import os
import tempfile
import unittest

# Point DATABASE_PATH to a temporary file for tests
test_db_fd, test_db_path = tempfile.mkstemp(suffix=".db")
os.close(test_db_fd)
os.environ["DATABASE_PATH"] = test_db_path

import app
import db


class DatasetCatalogTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Re-initialize clean test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        db.init_db()

    def tearDown(self):
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

    def test_healthz(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"healthy", response.data)

    def test_dashboard_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dataset Dashboard", response.data)
        self.assertIn(b"Global Climate Indicators", response.data)

    def test_list_and_search_datasets(self):
        # List all
        response = self.client.get("/datasets")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Global Climate Indicators", response.data)
        self.assertIn(b"Urban Mobility Survey", response.data)

        # Search for Climate
        response = self.client.get("/datasets?search=Climate")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Global Climate Indicators", response.data)
        self.assertNotIn(b"Urban Mobility Survey", response.data)

    def test_filter_by_format_category_license(self):
        # Filter by format CSV
        response = self.client.get("/datasets?format=CSV")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Global Climate Indicators", response.data)
        self.assertNotIn(b"Urban Mobility Survey", response.data)

        # Filter by category Biology
        response = self.client.get("/datasets?category=Biology")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Biodiversity Field Observations", response.data)
        self.assertNotIn(b"Global Climate Indicators", response.data)

        # Filter by license CC BY 4.0
        response = self.client.get("/datasets?license=CC+BY+4.0")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Global Climate Indicators", response.data)
        self.assertNotIn(b"Biodiversity Field Observations", response.data)

    def test_add_dataset(self):
        payload = {
            "name": "Neural Dynamics EEG",
            "description": "High-density EEG recordings from cognitive response experiments.",
            "category": "Neuroscience",
            "format": "JSON",
            "source": "https://example.com/neuro-data",
            "size": "4.2 GB",
            "license": "MIT",
        }
        response = self.client.post("/datasets/add", data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Neural Dynamics EEG", response.data)
        self.assertIn(b"Neuroscience", response.data)
        self.assertIn(b"4.2 GB", response.data)
        self.assertIn(b"MIT", response.data)

        # Verify it's persisted in the database
        datasets = db.get_all_datasets(search="Neural Dynamics")
        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0]["category"], "Neuroscience")

    def test_edit_dataset(self):
        # Update dataset 1
        updated_payload = {
            "name": "Updated Climate Dataset",
            "description": "Updated description with sufficient length for research.",
            "category": "Environmental Studies",
            "format": "Parquet",
            "source": "https://example.com/updated-climate",
            "size": "5.0 GB",
            "license": "Apache 2.0",
        }
        response = self.client.post("/datasets/1/edit", data=updated_payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Updated Climate Dataset", response.data)
        self.assertIn(b"Environmental Studies", response.data)

        # Verify DB directly
        dataset = db.get_dataset(1)
        self.assertEqual(dataset["name"], "Updated Climate Dataset")
        self.assertEqual(dataset["category"], "Environmental Studies")
        self.assertEqual(dataset["size"], "5.0 GB")

    def test_delete_dataset(self):
        # Delete dataset 1
        response = self.client.post("/datasets/1/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Global Climate Indicators", response.data)

        # Verify DB directly
        self.assertIsNone(db.get_dataset(1))


if __name__ == "__main__":
    unittest.main()
