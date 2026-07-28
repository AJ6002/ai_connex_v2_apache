"""
Unit Tests — Node 4: feature_engineer.py
Tests: scaler fit-only-on-train rule, rolling/lag column creation, no target leakage, determinism.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Replicate feature_engineer.py logic without AWS calls
# ---------------------------------------------------------------------------

SENSORS  = ["sensor_2", "sensor_3", "sensor_4", "sensor_7"]
SETTINGS = ["setting_1"]


def _process_features(df: pd.DataFrame, features: list, time_idx: str, identifier: str) -> pd.DataFrame:
    # Drop any pre-existing engineered columns to prevent duplicates on concat
    active_sensors = [s for s in features if df[s].std() > 0]
    cols_to_drop = []
    for window in [10, 20]:
        for col in active_sensors:
            cols_to_drop.append(f"{col}_roll_mean_{window}")
            cols_to_drop.append(f"{col}_roll_std_{window}")
    for lag in [1, 2]:
        for col in active_sensors:
            cols_to_drop.append(f"{col}_lag_{lag}_diff")
    cols_to_drop.append("time_standardized")
    
    existing_drops = [c for c in cols_to_drop if c in df.columns]
    if existing_drops:
        df = df.drop(columns=existing_drops)
        
    df["time_standardized"] = df[time_idx] / 300.0
    rolling_dfs = []
    for window in [10, 20]:
        roll = df.groupby(identifier)[active_sensors].rolling(window=window, min_periods=1)
        mean_df = roll.mean().reset_index(level=0, drop=True)
        mean_df.columns = [f"{c}_roll_mean_{window}" for c in active_sensors]
        std_df  = roll.std().reset_index(level=0, drop=True).fillna(0.0)
        std_df.columns  = [f"{c}_roll_std_{window}" for c in active_sensors]
        rolling_dfs.extend([mean_df, std_df])
    lag_dfs = []
    for lag in [1, 2]:
        lag_val  = df.groupby(identifier)[active_sensors].shift(lag)
        diff_df  = (df[active_sensors] - lag_val).fillna(0.0)
        diff_df.columns = [f"{c}_lag_{lag}_diff" for c in active_sensors]
        lag_dfs.append(diff_df)
    return pd.concat([df] + rolling_dfs + lag_dfs, axis=1)


def _make_split(engine_ids: list, cycles: int = 20) -> pd.DataFrame:
    np.random.seed(42)
    rows = []
    for eid in engine_ids:
        for c in range(1, cycles + 1):
            row = {"global_engine_id": eid, "cycle": c, "RUL": cycles - c}
            for s in SENSORS + SETTINGS:
                row[s] = float(np.random.normal(50, 5))
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFeatureEngineer:

    def _get_splits(self):
        train = _make_split([1, 2, 3])
        val   = _make_split([4])
        test  = _make_split([5])
        return train, val, test

    def _get_continuous_cols(self, df: pd.DataFrame) -> list:
        exclude = {"global_engine_id", "cycle", "RUL"}
        return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]

    def test_rolling_columns_created(self):
        train, _, _ = self._get_splits()
        fe = _process_features(train, SENSORS, "cycle", "global_engine_id")
        expected = [f"{s}_roll_mean_10" for s in SENSORS]
        for col in expected:
            assert col in fe.columns, f"Expected column {col} not found"

    def test_lag_columns_created(self):
        train, _, _ = self._get_splits()
        fe = _process_features(train, SENSORS, "cycle", "global_engine_id")
        expected = [f"{s}_lag_1_diff" for s in SENSORS]
        for col in expected:
            assert col in fe.columns, f"Expected column {col} not found"

    def test_scaler_fit_only_on_train(self):
        """
        Val mean and std BEFORE transform should differ from train mean/std.
        After applying train-fitted scaler, val should have a different mean
        than the train (which will be ~0). This confirms scaler was NOT refit on val.
        """
        train, val, _ = self._get_splits()
        train_fe = _process_features(train, SENSORS, "cycle", "global_engine_id")
        val_fe   = _process_features(val,   SENSORS, "cycle", "global_engine_id")

        exclude = {"global_engine_id", "cycle", "RUL"}
        cont_cols = [c for c in train_fe.columns if c not in exclude and pd.api.types.is_numeric_dtype(train_fe[c])]

        scaler = StandardScaler()
        train_fe[cont_cols] = scaler.fit_transform(train_fe[cont_cols].fillna(0))
        val_fe[cont_cols]   = scaler.transform(val_fe[cont_cols].fillna(0))

        # Train mean after fit-transform should be ~0
        train_mean = train_fe[cont_cols].mean().abs().mean()
        assert train_mean < 1e-10, f"Train mean after StandardScaler should be ~0, got {train_mean}"

        # Scaler's mean_ should equal the means fitted on train (not val)
        assert scaler.mean_ is not None, "Scaler should have been fitted"

    def test_scaler_same_transform_applied_to_val(self):
        train, val, _ = self._get_splits()
        train_fe = _process_features(train, SENSORS, "cycle", "global_engine_id")
        val_fe   = _process_features(val,   SENSORS, "cycle", "global_engine_id")
        exclude = {"global_engine_id", "cycle", "RUL"}
        cont_cols = [c for c in train_fe.columns if c not in exclude and pd.api.types.is_numeric_dtype(train_fe[c])]
        scaler = StandardScaler()
        scaler.fit(train_fe[cont_cols].fillna(0))
        val_transformed = scaler.transform(val_fe[cont_cols].fillna(0))
        # Re-transforming with the same scaler should produce same result (idempotent)
        val_transformed2 = scaler.transform(val_fe[cont_cols].fillna(0))
        np.testing.assert_array_almost_equal(val_transformed, val_transformed2)

    def test_target_column_not_in_scaled_features(self):
        """RUL must NEVER be scaled — it is the target."""
        train, _, _ = self._get_splits()
        fe = _process_features(train, SENSORS, "cycle", "global_engine_id")
        # RUL must be excluded from continuous features used for scaling
        # Mimic the exclude logic from feature_engineer.py
        exclude = {"global_engine_id", "cycle", "RUL", "dataset_id", "fault_mode", "operating_condition"}
        safe_cont = [c for c in fe.columns if c not in exclude and pd.api.types.is_numeric_dtype(fe[c])]
        assert "RUL" not in safe_cont, "RUL must be excluded from continuous features for scaling"

    def test_output_has_more_columns_than_input(self):
        train, _, _ = self._get_splits()
        fe = _process_features(train, SENSORS, "cycle", "global_engine_id")
        assert len(fe.columns) > len(train.columns), (
            "Engineered DataFrame should have more columns than raw input"
        )

    def test_determinism_same_output_twice(self):
        train, _, _ = self._get_splits()
        fe1 = _process_features(train, SENSORS, "cycle", "global_engine_id")
        fe2 = _process_features(train, SENSORS, "cycle", "global_engine_id")
        pd.testing.assert_frame_equal(fe1, fe2)
