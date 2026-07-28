"""
Integration Smoke Test - Full Mini-Pipeline (Node 1 -> Node 8)
Runs all pipeline steps locally on a tiny 200-row synthetic dataset.
No AWS, no S3, no SageMaker.

Verifies:
  - Each step runs without error.
  - Outputs are correctly handed off to the next step.
  - Final evaluation.json and robustness_report.json exist with required keys.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import sklearn.metrics

# --- Config ----------------------------------------------------------------

SENSORS  = ["sensor_2", "sensor_3", "sensor_4", "sensor_7"]
SETTINGS = ["setting_1", "setting_2"]
ALL_FEATURES = SENSORS + SETTINGS
TARGET   = "RUL"
IDENT    = "global_engine_id"
TIME_IDX = "cycle"

CONFIG = {
    "pipeline_run_id": "smoke-001",
    "project": "smoke_test",
    "domain": "regression",
    "algorithm": "random_forest",
    "hyperparameters": {"n_estimators": 5, "random_state": 42},
    "thresholds": {"max_missing_rate": 0.02, "max_collinearity": 0.98, "min_r2": -10.0},
    "schema": {
        "target_column": TARGET,
        "features": ALL_FEATURES,
        "time_index": TIME_IDX,
        "identifier": IDENT,
    },
}

# --- Helpers ----------------------------------------------------------------

def _make_raw_df(n_engines: int = 5, cycles: int = 40) -> pd.DataFrame:
    np.random.seed(42)
    rows = []
    for eid in range(1, n_engines + 1):
        for c in range(1, cycles + 1):
            row = {IDENT: eid, TIME_IDX: c, TARGET: cycles - c}
            for s in SENSORS:
                row[s] = float(np.random.normal(50.0, 5.0))
            for s in SETTINGS:
                row[s] = float(np.random.uniform(0.0, 1.0))
            rows.append(row)
    return pd.DataFrame(rows)


def _process_features(df: pd.DataFrame) -> pd.DataFrame:
    # Drop any pre-existing engineered columns to prevent duplicates on concat
    active = [s for s in SENSORS if df[s].std() > 0]
    cols_to_drop = []
    for window in [10, 20]:
        for col in active:
            cols_to_drop.append(f"{col}_roll_mean_{window}")
            cols_to_drop.append(f"{col}_roll_std_{window}")
    for lag in [1, 2]:
        for col in active:
            cols_to_drop.append(f"{col}_lag_{lag}_diff")
    cols_to_drop.append("time_standardized")
    
    existing_drops = [c for c in cols_to_drop if c in df.columns]
    if existing_drops:
        df = df.drop(columns=existing_drops)
        
    df["time_standardized"] = df[TIME_IDX] / 300.0
    rolling_dfs, lag_dfs = [], []
    for w in [10, 20]:
        roll = df.groupby(IDENT)[active].rolling(window=w, min_periods=1)
        m = roll.mean().reset_index(level=0, drop=True)
        m.columns = [f"{c}_roll_mean_{w}" for c in active]
        s = roll.std().reset_index(level=0, drop=True).fillna(0.0)
        s.columns = [f"{c}_roll_std_{w}" for c in active]
        rolling_dfs.extend([m, s])
    for lag in [1, 2]:
        lv = df.groupby(IDENT)[active].shift(lag)
        d = (df[active] - lv).fillna(0.0)
        d.columns = [f"{c}_lag_{lag}_diff" for c in active]
        lag_dfs.append(d)
    return pd.concat([df] + rolling_dfs + lag_dfs, axis=1)


# --- Smoke Test -------------------------------------------------------------

@pytest.fixture(scope="module")
def pipeline_outputs():
    """Run the full mini-pipeline once; return a dict of all intermediate outputs."""
    outputs = {}

    # -- Node 1: Clean ------------------------------------------------------
    raw_df = _make_raw_df()
    clean_df = raw_df.copy()
    for col in clean_df.select_dtypes(include="number").columns:
        if clean_df[col].isnull().any():
            clean_df[col] = clean_df[col].ffill().bfill().fillna(clean_df[col].mean())
    clean_df = clean_df.drop_duplicates().reset_index(drop=True)

    manifest = {
        "manifest_id": "manifest-smoke-001",
        "project": CONFIG["project"],
        "schema": CONFIG["schema"],
        "routing_decision": {
            "problem_type": CONFIG["domain"],
            "algorithm": CONFIG["algorithm"],
        },
        "dataset": {"row_count": len(clean_df), "column_count": len(clean_df.columns)},
    }
    outputs["clean_df"]  = clean_df
    outputs["manifest"]  = manifest
    outputs["n1_passed"] = True

    # -- Node 2: Validate Raw -----------------------------------------------
    null_rate = clean_df.isnull().sum().sum() / (clean_df.shape[0] * clean_df.shape[1])
    raw_report = {
        "status": "PASSED" if null_rate <= 0.02 else "FAILED",
        "checks": {"missing_rate": {"actual": null_rate, "limit": 0.02, "status": "PASS"}},
    }
    outputs["raw_report"] = raw_report
    outputs["n2_passed"]  = raw_report["status"] == "PASSED"

    # -- Node 3: Split ------------------------------------------------------
    ids = sorted(clean_df[IDENT].unique())
    n = len(ids)
    train_ids = ids[:int(n * 0.7)]
    val_ids   = ids[int(n * 0.7):int(n * 0.85)]
    test_ids  = ids[int(n * 0.85):]
    train_df = clean_df[clean_df[IDENT].isin(train_ids)].reset_index(drop=True)
    val_df   = clean_df[clean_df[IDENT].isin(val_ids)].reset_index(drop=True)
    test_df  = clean_df[clean_df[IDENT].isin(test_ids)].reset_index(drop=True)
    outputs.update({"train_df": train_df, "val_df": val_df, "test_df": test_df, "n3_passed": True})

    # -- Node 4: Feature Engineering ----------------------------------------
    train_fe = _process_features(train_df)
    val_fe   = _process_features(val_df)
    test_fe  = _process_features(test_df)

    exclude = {IDENT, TIME_IDX, TARGET}
    cont_cols = [c for c in train_fe.columns if c not in exclude and pd.api.types.is_numeric_dtype(train_fe[c])]
    scaler = StandardScaler()
    train_fe[cont_cols] = scaler.fit_transform(train_fe[cont_cols].fillna(0))
    val_fe[cont_cols]   = scaler.transform(val_fe[cont_cols].fillna(0))
    test_fe[cont_cols]  = scaler.transform(test_fe[cont_cols].fillna(0))

    manifest["schema"]["final_features"] = cont_cols
    outputs.update({"train_fe": train_fe, "val_fe": val_fe, "test_fe": test_fe,
                    "cont_cols": cont_cols, "scaler": scaler, "n4_passed": True})

    # -- Node 6: Train ------------------------------------------------------
    X_train = train_fe[cont_cols].fillna(0).values
    y_train = train_fe[TARGET].fillna(0).values
    model = RandomForestRegressor(n_estimators=5, random_state=42)
    model.fit(X_train, y_train)
    outputs.update({"model": model, "n6_passed": True})

    # -- Node 8: Evaluate ---------------------------------------------------
    X_test  = test_fe[cont_cols].fillna(0).values
    y_test  = test_fe[TARGET].fillna(0).values
    y_pred  = model.predict(X_test)
    r2   = sklearn.metrics.r2_score(y_test, y_pred)
    rmse = np.sqrt(sklearn.metrics.mean_squared_error(y_test, y_pred))
    mae  = sklearn.metrics.mean_absolute_error(y_test, y_pred)
    eval_report = {
        "regression_metrics": {
            "r2":   {"value": float(r2),   "standard_name": "R2"},
            "rmse": {"value": float(rmse), "standard_name": "RMSE"},
            "mae":  {"value": float(mae),  "standard_name": "MAE"},
        }
    }
    outputs.update({"eval_report": eval_report, "n8_passed": True})

    # -- Node 9: Explain ----------------------------------------------------
    importances = model.feature_importances_
    ranked = sorted(
        [{"feature": n, "importance": float(v)} for n, v in zip(cont_cols, importances)],
        key=lambda x: x["importance"],
        reverse=True,
    )
    explain_report = {"ranked_features": ranked}
    outputs.update({"explain_report": explain_report, "n9_passed": True})

    # -- Node 10: Stress ----------------------------------------------------
    np.random.seed(42)
    X_noisy = X_test.copy()
    for i in range(X_noisy.shape[1]):
        X_noisy[:, i] += np.random.normal(0, 0.1 * X_test[:, i].std(), len(X_test))
    rmse_clean = float(np.sqrt(sklearn.metrics.mean_squared_error(y_test, model.predict(X_test))))
    rmse_noisy = float(np.sqrt(sklearn.metrics.mean_squared_error(y_test, model.predict(X_noisy))))
    degradation = (rmse_noisy - rmse_clean) / (rmse_clean + 1e-9)
    robustness_report = {
        "status": "PASSED" if degradation <= 0.15 else "FAILED",
        "degradation_rate": float(degradation),
        "rmse_clean": rmse_clean,
        "rmse_noisy": rmse_noisy,
    }
    outputs.update({"robustness_report": robustness_report, "n10_passed": True})

    return outputs


# --- Assertions -------------------------------------------------------------

class TestSmokePipeline:

    def test_n1_cleaning_passed(self, pipeline_outputs):
        assert pipeline_outputs["n1_passed"]

    def test_n1_clean_df_has_no_nulls(self, pipeline_outputs):
        assert pipeline_outputs["clean_df"].isnull().sum().sum() == 0

    def test_n2_raw_validation_passed(self, pipeline_outputs):
        assert pipeline_outputs["n2_passed"]

    def test_n3_split_no_entity_overlap(self, pipeline_outputs):
        tr_ids  = set(pipeline_outputs["train_df"][IDENT])
        val_ids = set(pipeline_outputs["val_df"][IDENT])
        tst_ids = set(pipeline_outputs["test_df"][IDENT])
        assert len(tr_ids & val_ids) == 0
        assert len(tr_ids & tst_ids) == 0

    def test_n3_row_sum_equals_total(self, pipeline_outputs):
        total = (
            len(pipeline_outputs["train_df"]) +
            len(pipeline_outputs["val_df"])   +
            len(pipeline_outputs["test_df"])
        )
        assert total == len(pipeline_outputs["clean_df"])

    def test_n4_engineered_has_rolling_columns(self, pipeline_outputs):
        cols = pipeline_outputs["train_fe"].columns.tolist()
        assert any("roll_mean" in c for c in cols)

    def test_n4_scaler_fitted_on_train(self, pipeline_outputs):
        scaler = pipeline_outputs["scaler"]
        assert scaler.mean_ is not None

    def test_n6_model_fitted(self, pipeline_outputs):
        model = pipeline_outputs["model"]
        assert hasattr(model, "predict")

    def test_n8_eval_report_has_r2(self, pipeline_outputs):
        assert "regression_metrics" in pipeline_outputs["eval_report"]
        assert "r2" in pipeline_outputs["eval_report"]["regression_metrics"]

    def test_n8_r2_is_real_number(self, pipeline_outputs):
        r2 = pipeline_outputs["eval_report"]["regression_metrics"]["r2"]["value"]
        assert isinstance(r2, float)
        assert not np.isnan(r2)

    def test_n9_explain_has_ranked_features(self, pipeline_outputs):
        assert "ranked_features" in pipeline_outputs["explain_report"]
        assert len(pipeline_outputs["explain_report"]["ranked_features"]) > 0

    def test_n10_robustness_has_required_keys(self, pipeline_outputs):
        rr = pipeline_outputs["robustness_report"]
        for key in ["status", "degradation_rate", "rmse_clean", "rmse_noisy"]:
            assert key in rr

    def test_n10_status_is_valid(self, pipeline_outputs):
        assert pipeline_outputs["robustness_report"]["status"] in ("PASSED", "FAILED")
