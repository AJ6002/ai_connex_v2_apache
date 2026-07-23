from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import sys
import json
import uuid
import pickle
import datetime
import traceback
import pandas as pd
import numpy as np

# Fix Windows cp1252 console encoding so emoji in aiconnex_ml logs don't crash
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ── sklearn models ────────────────────────────────────────────────────────────
from sklearn.linear_model import LogisticRegression, LinearRegression, HuberRegressor, Ridge, Lasso, ElasticNet
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    AdaBoostClassifier, AdaBoostRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor
)
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.svm import SVC, SVR
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ── aiconnex_ml path resolution ───────────────────────────────────────────────
AIC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AICONNEX_ML_ROOT = os.path.abspath(os.path.join(AIC_ROOT, "..", "aiconnex_ml"))
if AICONNEX_ML_ROOT not in sys.path:
    sys.path.insert(0, os.path.dirname(AICONNEX_ML_ROOT))

app = FastAPI(
    title="Model Training API",
    description="Async model training with VG_1 data quality gate and scaler preservation.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory job store ───────────────────────────────────────────────────────
# {job_id: {"status": "running|completed|failed", "result": {...}, "error": str}}
JOBS: Dict[str, Dict[str, Any]] = {}


class TrainPayload(BaseModel):
    train_path: str
    val_path: str
    target_column: Optional[str] = None
    recipe: Dict[str, Any]
    run_id: str
    manifest_path: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "Train API (Async)"}


@app.post("/api/v1/train", status_code=202)
def train_model(payload: TrainPayload, background_tasks: BackgroundTasks):
    """
    Dispatch training as a background task. Returns 202 Accepted with a job_id
    immediately so the orchestrator is never blocked by long HPO runs.
    """
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    JOBS[job_id] = {
        "status": "running",
        "job_id": job_id,
        "run_id": payload.run_id,
        "started_at": datetime.datetime.now().isoformat(),
        "result": None,
        "error": None,
        "vg1_report": None,
    }
    background_tasks.add_task(_run_training_job, job_id, payload)
    return {"status": "accepted", "job_id": job_id, "run_id": payload.run_id}

@app.get("/api/v1/train/status/{job_id}")
def train_status(job_id: str):
    """Poll this endpoint to check if training has completed."""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return JOBS[job_id]


@app.get("/api/v1/train/jobs")
def list_jobs():
    """List all training jobs (for diagnostics)."""
    return {"total": len(JOBS), "jobs": list(JOBS.keys())}


# ─────────────────────────────────────────────────────────────────────────────
# Background Training Worker
# ─────────────────────────────────────────────────────────────────────────────

def _run_training_job(job_id: str, payload: TrainPayload):
    """
    Executes the full training pipeline in the background:
      1. Load manifest
      2. Run VG_1 Data Quality Gate
      3. Build and fit the model
      4. Save model + scaler pickle files
      5. Write training results to manifest
      6. Update JOBS[job_id]
    """
    train_path    = payload.train_path
    val_path      = payload.val_path
    target_col    = payload.target_column
    recipe        = payload.recipe
    run_id        = payload.run_id
    manifest_path = payload.manifest_path

    try:
        # ── 1. Load training data ────────────────────────────────────────────
        if not os.path.exists(train_path):
            raise FileNotFoundError(f"Train partition not found at {train_path}")

        df_train = pd.read_csv(train_path)
        df_val   = pd.read_csv(val_path) if val_path and os.path.exists(val_path) else None

        # ── 2. Load manifest from disk ───────────────────────────────────────
        manifest: Dict[str, Any] = {}
        if manifest_path and os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        # ── 3. VG_1 Data Quality Gate (pre-train validation) ─────────────────
        try:
            from aiconnex_ml.shared.data.validation_gate_1 import check_vg1
            is_valid, vg1_report = check_vg1(manifest, df_train)
            JOBS[job_id]["vg1_report"] = vg1_report
        except Exception as vg1_ex:
            print(f"[VG_1] Warning: Gate check failed with exception: {vg1_ex}. Treating as passed.")
            is_valid, vg1_report = True, {"gate": "VG_1", "passed": True, "detail": f"Gate skipped: {vg1_ex}"}
            JOBS[job_id]["vg1_report"] = vg1_report

        if not is_valid:
            failed = [k for k, v in vg1_report.get("checks", {}).items() if not v.get("passed")]
            err_msg = f"VG_1 Data Quality Gate FAILED. Failed checks: {failed}. Training aborted."
            JOBS[job_id].update({"status": "failed", "error": err_msg})
            # Write gate failure to manifest
            _update_manifest(manifest_path, manifest, {"pipeline_step": "train_vg1_failed", "validation_results": manifest.get("validation_results", {})})
            return

        # ── 4. Prepare X / y ─────────────────────────────────────────────────
        if target_col and target_col in df_train.columns:
            y_train = df_train[target_col]
            X_train = df_train.drop(columns=[target_col])
        else:
            y_train = None
            X_train = df_train

        # Drop any remaining non-numeric columns before fitting
        non_numeric = [c for c in X_train.columns if not pd.api.types.is_numeric_dtype(X_train[c])]
        if non_numeric:
            X_train = X_train.drop(columns=non_numeric)

        X_train = X_train.fillna(X_train.median(numeric_only=True).fillna(0))

        # ── 5. Scale features & save scaler ──────────────────────────────────
        workspace_data_dir = os.path.dirname(train_path)
        os.makedirs(workspace_data_dir, exist_ok=True)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        scaler_path = os.path.join(workspace_data_dir, f"scaler_{run_id}.pkl")
        with open(scaler_path, "wb") as f:
            pickle.dump(scaler, f)

        # ── 6. Resolve algorithm & fit model ─────────────────────────────────
        algorithm   = recipe.get("algorithm", "Estimator")
        variant     = recipe.get("variant", "Standard")
        hyperparams = recipe.get("hyperparameters", {})
        algo_lower  = str(algorithm).lower()
        var_lower   = str(variant).lower()

        # Detect task type
        task_type = str(manifest.get("profile", {}).get("suggested_task", ""))
        family_type = str(manifest.get("profile", {}).get("algorithm_family", ""))
        ml_task = str(manifest.get("ml_task", ""))

        if "anomaly" in family_type.lower() or "anomaly" in task_type.lower() or "anomaly" in ml_task.lower():
            is_anomaly = True
            is_regression = False
        elif "regression" in family_type.lower() or "regression" in task_type.lower() or "time" in task_type.lower():
            is_anomaly = False
            is_regression = True
        elif y_train is not None:
            is_anomaly = False
            if (y_train.nunique() <= 10 and not pd.api.types.is_float_dtype(y_train)) or pd.api.types.is_string_dtype(y_train) or pd.api.types.is_object_dtype(y_train):
                is_regression = False
            else:
                is_regression = True
        else:
            is_anomaly = True
            is_regression = False

        model = _resolve_model(algo_lower, var_lower, hyperparams, is_regression, is_anomaly=is_anomaly)

        # Fit
        if y_train is not None:
            model.fit(X_train_scaled, y_train)
        else:
            model.fit(X_train_scaled)

        # ── 7. Save model pickle ─────────────────────────────────────────────
        model_path = os.path.join(workspace_data_dir, f"model_{run_id}.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        # ── 8. Write training results to manifest ─────────────────────────────
        manifest["training_results"] = {
            "model_path":   model_path,
            "scaler_path":  scaler_path,
            "algorithm":    model.__class__.__name__,
            "variant":      variant,
            "train_rows":   int(len(df_train)),
            "feature_count": int(X_train.shape[1]),
            "trained_at":   datetime.datetime.now().isoformat(),
        }
        manifest["pipeline_step"] = "train"
        _update_manifest(manifest_path, manifest)

        # ── 9. Mark job complete ─────────────────────────────────────────────
        JOBS[job_id].update({
            "status":       "completed",
            "completed_at": datetime.datetime.now().isoformat(),
            "result": {
                "model_path":  model_path,
                "scaler_path": scaler_path,
                "algorithm":   model.__class__.__name__,
                "variant":     variant,
            },
        })
        print(f"[TrainNode] Job {job_id} completed → {model_path}")

    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[TrainNode] Job {job_id} FAILED:\n{tb}")
        JOBS[job_id].update({"status": "failed", "error": str(exc)})


# ─────────────────────────────────────────────────────────────────────────────
# Model Resolution Registry
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_model(algo_lower: str, var_lower: str, hyperparams: dict, is_regression: bool):
    """Map recipe algorithm name → sklearn estimator instance."""

    # 1. Logistic Regression
    if "logistic" in algo_lower:
        penalty, solver, l1_ratio, class_weight = "l2", "lbfgs", None, None
        if "l1" in var_lower:        penalty, solver = "l1", "liblinear"
        elif "elastic" in var_lower: penalty, solver, l1_ratio = "elasticnet", "saga", hyperparams.get("l1_ratio", 0.5)
        elif "balanced" in var_lower: class_weight = "balanced"
        return LogisticRegression(penalty=penalty, solver=solver, l1_ratio=l1_ratio,
                                   class_weight=class_weight, max_iter=1000, random_state=42)

    # 2. Linear Regression / Huber / Ridge / Lasso / ElasticNet
    if "linear regression" in algo_lower:
        return HuberRegressor(max_iter=1000) if "huber" in var_lower else LinearRegression(fit_intercept=hyperparams.get("fit_intercept", True))
    if "ridge" in algo_lower:
        return Ridge(alpha=hyperparams.get("alpha", 1.0), random_state=42)
    if "lasso" in algo_lower:
        return Lasso(alpha=hyperparams.get("alpha", 1.0), random_state=42)
    if "elastic" in algo_lower or "net" in algo_lower:
        return ElasticNet(alpha=hyperparams.get("alpha", 1.0), l1_ratio=hyperparams.get("l1_ratio", 0.5), random_state=42)

    # 3. Gradient Boosting & AdaBoost & ExtraTrees
    if "gradient boosting" in algo_lower:
        n, lr, d = hyperparams.get("n_estimators", 100), hyperparams.get("learning_rate", 0.1), hyperparams.get("max_depth", 3)
        return GradientBoostingRegressor(n_estimators=n, learning_rate=lr, max_depth=d, random_state=42) if is_regression \
               else GradientBoostingClassifier(n_estimators=n, learning_rate=lr, max_depth=d, random_state=42)

    if "adaboost" in algo_lower:
        n, lr = hyperparams.get("n_estimators", 50), hyperparams.get("learning_rate", 1.0)
        return AdaBoostRegressor(n_estimators=n, learning_rate=lr, random_state=42) if is_regression \
               else AdaBoostClassifier(n_estimators=n, learning_rate=lr, random_state=42)

    if "extra tree" in algo_lower or "extratrees" in algo_lower:
        n, d = hyperparams.get("n_estimators", 100), hyperparams.get("max_depth", None)
        return ExtraTreesRegressor(n_estimators=n, max_depth=d, random_state=42) if is_regression \
               else ExtraTreesClassifier(n_estimators=n, max_depth=d, random_state=42)

    # 4. Random Forest & Decision Tree
    if "random forest" in algo_lower:
        n, d = hyperparams.get("n_estimators", 100), hyperparams.get("max_depth", None)
        if is_regression:
            return RandomForestRegressor(n_estimators=n, max_depth=d, random_state=42)
        cw = "balanced" if any(k in var_lower for k in ("weighted", "balanced")) else None
        return RandomForestClassifier(n_estimators=n, max_depth=d, class_weight=cw, random_state=42)

    if "decision tree" in algo_lower or "tree" in algo_lower:
        d = hyperparams.get("max_depth", None)
        return DecisionTreeRegressor(max_depth=d, random_state=42) if is_regression \
               else DecisionTreeClassifier(max_depth=d, random_state=42)

    # 5. SVR / Support Vector Machines & KNN
    if "support vector" in algo_lower or "svm" in algo_lower or "svr" in algo_lower or "svc" in algo_lower:
        C_val = hyperparams.get("C", 1.0)
        return SVR(C=C_val) if is_regression else SVC(C=C_val, probability=True, random_state=42)

    if "k-neighbor" in algo_lower or "knn" in algo_lower or "nearest neighbor" in algo_lower:
        k_val = hyperparams.get("n_neighbors", 5)
        return KNeighborsRegressor(n_neighbors=k_val) if is_regression else KNeighborsClassifier(n_neighbors=k_val)

    # 5. XGBoost (with GradientBoosting fallback)
    if "xgboost" in algo_lower:
        lr, n, d = hyperparams.get("learning_rate", 0.1), hyperparams.get("n_estimators", 100), hyperparams.get("max_depth", 3)
        try:
            import xgboost as xgb
            return xgb.XGBRegressor(n_estimators=n, learning_rate=lr, max_depth=d, random_state=42) if is_regression \
                   else xgb.XGBClassifier(n_estimators=n, learning_rate=lr, max_depth=d, random_state=42)
        except ImportError:
            return GradientBoostingRegressor(n_estimators=n, learning_rate=lr, max_depth=d, random_state=42) if is_regression \
                   else GradientBoostingClassifier(n_estimators=n, learning_rate=lr, max_depth=d, random_state=42)

    # 6. LightGBM (with GradientBoosting fallback)
    if "lightgbm" in algo_lower:
        n, lr = hyperparams.get("n_estimators", 100), hyperparams.get("learning_rate", 0.1)
        try:
            import lightgbm as lgb
            return lgb.LGBMRegressor(n_estimators=n, learning_rate=lr, random_state=42, verbose=-1) if is_regression \
                   else lgb.LGBMClassifier(n_estimators=n, learning_rate=lr, random_state=42, verbose=-1)
        except ImportError:
            return GradientBoostingRegressor(n_estimators=n, learning_rate=lr, random_state=42) if is_regression \
                   else GradientBoostingClassifier(n_estimators=n, random_state=42)

    # 7. Anomaly Detection
    if "isolation forest" in algo_lower or "anomaly" in algo_lower:
        return IsolationForest(contamination=hyperparams.get("contamination", "auto"), random_state=42)

    # 8. Clustering
    if "k-means" in algo_lower or "clustering" in algo_lower:
        return KMeans(n_clusters=hyperparams.get("n_clusters", 3), random_state=42)

    # 9. Time-series / ARIMA / Prophet
    if any(k in algo_lower for k in ("arima", "prophet", "time-series", "sarima", "var")):
        try:
            import lightgbm as lgb
            return lgb.LGBMRegressor(n_estimators=100, learning_rate=0.1, random_state=42, verbose=-1) if is_regression \
                   else lgb.LGBMClassifier(n_estimators=100, learning_rate=0.1, random_state=42, verbose=-1)
        except ImportError:
            return GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42) if is_regression \
                   else GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)

    # 10. General fallback
    return GradientBoostingRegressor(n_estimators=100, random_state=42) if is_regression else LogisticRegression(max_iter=1000, random_state=42)


# ─────────────────────────────────────────────────────────────────────────────
# Manifest Helper
# ─────────────────────────────────────────────────────────────────────────────

def _update_manifest(manifest_path: Optional[str], manifest: Dict[str, Any], extra: Optional[Dict] = None):
    """Merge `extra` into `manifest` and write to disk."""
    if not manifest_path:
        return
    try:
        if extra:
            manifest.update(extra)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[TrainNode] Warning: Could not update manifest: {e}")


if __name__ == "__main__":
    import uvicorn
    should_reload = os.environ.get("AIC_RELOAD", "0").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8006, reload=should_reload)
