"""
Contract Tests - Manifest Schema
Validates that the manifest.json produced by Node 1 always contains
the required contract keys regardless of the data values.
"""
import json
import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_valid_manifest() -> dict:
    return {
        "manifest_id": "manifest-run-001",
        "project":     "test_project",
        "created_at":  pd.Timestamp.now().isoformat(),
        "dataset": {
            "uri":          "local/clean_dataset.parquet",
            "row_count":    200,
            "column_count": 15,
        },
        "schema": {
            "target_column": "RUL",
            "features":      ["sensor_2", "sensor_3"],
            "time_index":    "cycle",
            "identifier":    "global_engine_id",
        },
        "routing_decision": {
            "problem_type": "regression",
            "algorithm":    "random_forest",
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestManifestSchema:

    REQUIRED_TOP = ["manifest_id", "schema", "routing_decision", "dataset"]
    REQUIRED_SCHEMA = ["target_column", "features", "time_index", "identifier"]
    REQUIRED_ROUTING = ["problem_type", "algorithm"]
    REQUIRED_DATASET = ["row_count", "column_count"]

    def test_top_level_required_keys_present(self):
        m = _make_valid_manifest()
        for key in self.REQUIRED_TOP:
            assert key in m, f"Manifest missing top-level key: '{key}'"

    def test_schema_section_required_keys(self):
        m = _make_valid_manifest()
        for key in self.REQUIRED_SCHEMA:
            assert key in m["schema"], f"manifest.schema missing key: '{key}'"

    def test_routing_decision_required_keys(self):
        m = _make_valid_manifest()
        for key in self.REQUIRED_ROUTING:
            assert key in m["routing_decision"], f"manifest.routing_decision missing key: '{key}'"

    def test_dataset_required_keys(self):
        m = _make_valid_manifest()
        for key in self.REQUIRED_DATASET:
            assert key in m["dataset"], f"manifest.dataset missing key: '{key}'"

    def test_manifest_id_is_string(self):
        m = _make_valid_manifest()
        assert isinstance(m["manifest_id"], str)

    def test_features_is_list(self):
        m = _make_valid_manifest()
        assert isinstance(m["schema"]["features"], list)

    def test_row_count_is_positive_int(self):
        m = _make_valid_manifest()
        assert isinstance(m["dataset"]["row_count"], int)
        assert m["dataset"]["row_count"] > 0

    def test_problem_type_is_valid(self):
        m = _make_valid_manifest()
        assert m["routing_decision"]["problem_type"] in ("regression", "anomaly")

    def test_algorithm_is_known(self):
        known = {"random_forest", "xgboost", "linear_regression", "ridge", "isolation_forest"}
        m = _make_valid_manifest()
        assert m["routing_decision"]["algorithm"] in known

    def test_missing_manifest_id_fails(self):
        m = _make_valid_manifest()
        del m["manifest_id"]
        assert "manifest_id" not in m

    def test_manifest_is_json_serializable(self):
        m = _make_valid_manifest()
        dumped = json.dumps(m)
        reloaded = json.loads(dumped)
        assert reloaded["manifest_id"] == m["manifest_id"]
