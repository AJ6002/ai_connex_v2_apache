"""
Unit Tests — Node 9: explain.py
Tests: feature importance extraction, ranked_features schema, score ordering.
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor


# ---------------------------------------------------------------------------
# Replicate explain.py core feature-importance logic without AWS calls
# ---------------------------------------------------------------------------

FEATURES = ["sensor_2", "sensor_3", "sensor_4", "sensor_7"]


def _compute_feature_importance(model, feature_names: list) -> dict:
    importances = model.feature_importances_
    ranked = sorted(
        [{"feature": n, "importance": float(v)} for n, v in zip(feature_names, importances)],
        key=lambda x: x["importance"],
        reverse=True,
    )
    return {"ranked_features": ranked}


def _fit_rf(n: int = 80) -> RandomForestRegressor:
    np.random.seed(42)
    X = np.random.normal(50, 5, (n, len(FEATURES)))
    y = np.random.randint(0, 80, n).astype(float)
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    return model


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExplain:

    def test_output_has_ranked_features_key(self):
        model = _fit_rf()
        result = _compute_feature_importance(model, FEATURES)
        assert "ranked_features" in result

    def test_ranked_features_is_list(self):
        model = _fit_rf()
        result = _compute_feature_importance(model, FEATURES)
        assert isinstance(result["ranked_features"], list)

    def test_ranked_features_nonempty(self):
        model = _fit_rf()
        result = _compute_feature_importance(model, FEATURES)
        assert len(result["ranked_features"]) > 0

    def test_ranked_features_count_matches_features(self):
        model = _fit_rf()
        result = _compute_feature_importance(model, FEATURES)
        assert len(result["ranked_features"]) == len(FEATURES)

    def test_each_entry_has_feature_and_importance_keys(self):
        model = _fit_rf()
        result = _compute_feature_importance(model, FEATURES)
        for entry in result["ranked_features"]:
            assert "feature" in entry
            assert "importance" in entry

    def test_importances_are_floats(self):
        model = _fit_rf()
        result = _compute_feature_importance(model, FEATURES)
        for entry in result["ranked_features"]:
            assert isinstance(entry["importance"], float)

    def test_importances_sum_to_approx_1(self):
        model = _fit_rf()
        result = _compute_feature_importance(model, FEATURES)
        total = sum(e["importance"] for e in result["ranked_features"])
        assert abs(total - 1.0) < 1e-6, f"Importances should sum to ~1.0, got {total}"

    def test_ranked_in_descending_order(self):
        model = _fit_rf()
        result = _compute_feature_importance(model, FEATURES)
        scores = [e["importance"] for e in result["ranked_features"]]
        assert scores == sorted(scores, reverse=True), "Features should be in descending importance order"

    def test_all_feature_names_present(self):
        model = _fit_rf()
        result = _compute_feature_importance(model, FEATURES)
        names = {e["feature"] for e in result["ranked_features"]}
        assert names == set(FEATURES)
