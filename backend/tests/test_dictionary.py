"""
Tests for the Data Dictionary module.

Covers:
- Loading seed data on startup populates feature entries correctly
- upsert_entry/delete_entry reject entry_type="feature"
- upsert_entry on content-source persists across reload
- list_entries(entry_type="sop") returns only SOP entries
- Flask routes return correct status codes
"""

import json
import os
import sys
import tempfile
import unittest
from copy import deepcopy

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dictionary.schemas import DictionaryEntry, FeatureFields, KnowledgeBaseFields, CheatSheetFields, PolicyManualFields, SopFields, MacroTemplateFields
from dictionary.store import (
    get_entry,
    list_entries,
    upsert_entry,
    delete_entry,
    initialize,
    _FEATURE_STORE,
    _CONTENT_STORE,
)
from dictionary.loader import load_dictionary


class TestStoreLoading(unittest.TestCase):
    """Test that seed data loads correctly."""

    def setUp(self):
        """Reload stores before each test."""
        initialize()

    def test_feature_seed_loads(self):
        """Loading seed data should populate feature entries."""
        entries = list_entries(entry_type="feature")
        self.assertGreater(len(entries), 0)
        # Check that our known feature entries exist
        feature_ids = [e.entry_id for e in entries]
        self.assertIn("feature_voltage", feature_ids)
        self.assertIn("feature_temperature", feature_ids)
        self.assertIn("feature_pressure", feature_ids)

    def test_feature_entry_fields(self):
        """Feature entries should have correct field values."""
        entry = get_entry("feature_voltage")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.entry_type, "feature")
        self.assertEqual(entry.display_name, "Voltage")
        self.assertIsNotNone(entry.feature_fields)
        self.assertEqual(entry.feature_fields.data_type, "float")
        self.assertEqual(entry.feature_fields.physical_unit, "V")
        self.assertEqual(entry.feature_fields.expected_range, [0, 480])
        self.assertEqual(entry.feature_fields.null_gate_ratio, 0.05)
        self.assertEqual(entry.feature_fields.stuck_limit_rows, 100)
        self.assertEqual(entry.feature_fields.imputation_fallback, "forward_fill")

    def test_content_store_loads(self):
        """Content-source entries should load from data file."""
        entries = list_entries()
        # Should have 5 content-source entries + 3 feature entries
        self.assertGreaterEqual(len(entries), 5)
        content_ids = [e.entry_id for e in entries if e.entry_type != "feature"]
        self.assertIn("kb_001", content_ids)
        self.assertIn("cs_001", content_ids)
        self.assertIn("pm_001", content_ids)
        self.assertIn("sop_001", content_ids)
        self.assertIn("mt_001", content_ids)


class TestUpsertDeleteRejectFeature(unittest.TestCase):
    """Test that upsert/delete reject feature entries."""

    def setUp(self):
        initialize()

    def test_upsert_feature_raises_error(self):
        """upsert_entry should raise ValueError for entry_type='feature'."""
        feature_entry = DictionaryEntry(
            entry_id="feature_test",
            entry_type="feature",
            display_name="Test Feature",
            feature_fields=FeatureFields(data_type="float"),
        )
        with self.assertRaises(ValueError) as ctx:
            upsert_entry(feature_entry)
        self.assertIn("Cannot upsert entry_type='feature'", str(ctx.exception))

    def test_delete_feature_raises_error(self):
        """delete_entry should raise ValueError for feature entries."""
        with self.assertRaises(ValueError) as ctx:
            delete_entry("feature_voltage")
        self.assertIn("Cannot delete entry_id='feature_voltage'", str(ctx.exception))
        self.assertIn("entry_type='feature'", str(ctx.exception))

    def test_delete_nonexistent_returns_false(self):
        """delete_entry should return False for non-existent IDs."""
        result = delete_entry("nonexistent_id")
        self.assertFalse(result)


class TestUpsertPersistence(unittest.TestCase):
    """Test that upsert_entry persists across reloads."""

    def setUp(self):
        self._original_data_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "dictionary_entries.json"
        )
        # Use a temp file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_data_path = os.path.join(self.temp_dir, "dictionary_entries.json")
        # Copy original data to temp
        import shutil
        shutil.copy(self._original_data_path, self.temp_data_path)

    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_upsert_persists_after_reload(self):
        """Upserting an entry should persist when the store is reloaded."""
        # Create a new entry
        new_entry = DictionaryEntry(
            entry_id="kb_test",
            entry_type="knowledge_base",
            display_name="Test Knowledge Base",
            description="A test entry",
            created_at="2024-01-01T00:00:00Z",
            tags=["test"],
            knowledge_base_fields=KnowledgeBaseFields(
                source_path="/kb/test.md",
                article_count=5,
                search_index_ref="kb-idx-test",
            ),
        )

        # Manually load into store
        initialize()

        # Upsert the entry
        result = upsert_entry(new_entry)

        # Verify it's in the store
        entry = get_entry("kb_test")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.display_name, "Test Knowledge Base")

        # Simulate reload by re-initializing
        initialize()

        # Verify it's still there
        entry = get_entry("kb_test")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.display_name, "Test Knowledge Base")


class TestListEntriesFiltering(unittest.TestCase):
    """Test list_entries filtering by entry_type."""

    def setUp(self):
        initialize()

    def test_list_all_entries(self):
        """list_entries() with no filter should return all entries."""
        entries = list_entries()
        self.assertGreaterEqual(len(entries), 8)  # 3 features + 5 content

    def test_list_feature_entries(self):
        """list_entries(entry_type='feature') should return only features."""
        entries = list_entries(entry_type="feature")
        self.assertEqual(len(entries), 3)
        for e in entries:
            self.assertEqual(e.entry_type, "feature")

    def test_list_sop_entries(self):
        """list_entries(entry_type='sop') should return only SOPs."""
        entries = list_entries(entry_type="sop")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].entry_type, "sop")
        self.assertEqual(entries[0].entry_id, "sop_001")

    def test_list_knowledge_base_entries(self):
        """list_entries(entry_type='knowledge_base') should return only KB entries."""
        entries = list_entries(entry_type="knowledge_base")
        self.assertGreaterEqual(len(entries), 1)
        for e in entries:
            self.assertEqual(e.entry_type, "knowledge_base")

    def test_list_nonexistent_type_returns_empty(self):
        """list_entries with a type that doesn't exist should return empty list."""
        entries = list_entries(entry_type="nonexistent_type")
        self.assertEqual(len(entries), 0)


class TestFlaskRoutes(unittest.TestCase):
    """Test Flask route responses."""

    def setUp(self):
        from app import app
        self.app = app
        self.client = self.app.test_client()
        initialize()

    def test_list_entries_route(self):
        """GET /api/dictionary/entries should return all entries."""
        response = self.client.get("/api/dictionary/entries")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 8)

    def test_list_entries_with_filter(self):
        """GET /api/dictionary/entries?entry_type=feature should filter."""
        response = self.client.get("/api/dictionary/entries?entry_type=feature")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 3)
        for entry in data:
            self.assertEqual(entry["entry_type"], "feature")

    def test_get_entry_route(self):
        """GET /api/dictionary/entries/<id> should return one entry."""
        response = self.client.get("/api/dictionary/entries/feature_voltage")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["entry_id"], "feature_voltage")
        self.assertEqual(data["display_name"], "Voltage")

    def test_get_entry_not_found(self):
        """GET /api/dictionary/entries/<id> should 404 for missing entries."""
        response = self.client.get("/api/dictionary/entries/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_create_content_source_entry(self):
        """POST /api/dictionary/entries should create a content-source entry."""
        new_entry = {
            "entry_id": "kb_test",
            "entry_type": "knowledge_base",
            "display_name": "Test KB",
            "description": "Test entry",
            "created_at": "2024-01-01T00:00:00Z",
            "tags": ["test"],
            "knowledge_base_fields": {
                "source_path": "/kb/test.md",
                "article_count": 1,
                "search_index_ref": "test-idx",
            },
        }
        response = self.client.post(
            "/api/dictionary/entries",
            data=json.dumps(new_entry),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data["entry_id"], "kb_test")

    def test_create_feature_entry_rejected(self):
        """POST /api/dictionary/entries should reject feature entries."""
        feature_entry = {
            "entry_id": "feature_test",
            "entry_type": "feature",
            "display_name": "Test Feature",
            "feature_fields": {
                "data_type": "float",
                "physical_unit": "V",
                "expected_range": [0, 100],
                "null_gate_ratio": 0.05,
                "stuck_limit_rows": 10,
                "imputation_fallback": "forward_fill",
            },
        }
        response = self.client.post(
            "/api/dictionary/entries",
            data=json.dumps(feature_entry),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_create_invalid_entry_returns_400(self):
        """POST /api/dictionary/entries with invalid data should return 400."""
        invalid_entry = {
            "entry_id": "test",
            # Missing required fields
        }
        response = self.client.post(
            "/api/dictionary/entries",
            data=json.dumps(invalid_entry),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_content_source_entry(self):
        """DELETE /api/dictionary/entries/<id> should delete content-source entries."""
        # Create an entry first (since kb_001 may have been deleted in a previous test run)
        new_entry = {
            "entry_id": "kb_delete_test",
            "entry_type": "knowledge_base",
            "display_name": "Test KB for Deletion",
            "description": "Test entry",
            "created_at": "2024-01-01T00:00:00Z",
            "tags": ["test"],
            "knowledge_base_fields": {
                "source_path": "/kb/delete-test.md",
                "article_count": 1,
                "search_index_ref": "test-idx",
            },
        }
        self.client.post(
            "/api/dictionary/entries",
            data=json.dumps(new_entry),
            content_type="application/json",
        )

        # Now delete it
        response = self.client.delete("/api/dictionary/entries/kb_delete_test")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["deleted"], "kb_delete_test")

        # Verify it's gone
        response = self.client.get("/api/dictionary/entries/kb_delete_test")
        self.assertEqual(response.status_code, 404)

    def test_delete_feature_entry_rejected(self):
        """DELETE /api/dictionary/entries/<id> should reject feature entries."""
        response = self.client.delete("/api/dictionary/entries/feature_voltage")
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_delete_nonexistent_entry_returns_404(self):
        """DELETE /api/dictionary/entries/<id> should 404 for missing entries."""
        response = self.client.delete("/api/dictionary/entries/nonexistent")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()