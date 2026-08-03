# ML Pipeline Architecture: From Notebooks to Production Engine

## The Problem with What We Have Today

The current notebook fleet (01–10) works. But it has a critical structural weakness: **all the ML logic lives inside notebook cells.** This means:

- You cannot unit-test a feature engineering function without opening Colab.
- You cannot reuse the same training logic in a SageMaker step, an Airflow DAG, or an edge container without copy-pasting code.
- You cannot version-control notebook diffs cleanly (JSON blobs are unmergeable in Git).
- A typo in Cell 7 of Notebook 6 silently breaks the entire downstream pipeline.

The architecture direction you identified solves all of this. Here is the research-backed breakdown.

---

## The 6-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 6: OPTIONAL CLOUD SYNC                     │
│  S3 artifact store · MLflow tracking · Remote monitoring dashboard  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ (optional push/pull)
┌────────────────────────────────▼────────────────────────────────────┐
│                  LAYER 5: CONTAINERIZED EXECUTION                   │
│  Docker image per task · ONNX/Treelite compiled models · FastAPI    │
│  Runs on: Edge PC, On-Prem Server, Colab, SageMaker, K3s cluster   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                 LAYER 4: PORTABLE MANIFEST BACKEND                  │
│  manifest.json = single source of truth for the entire run          │
│  Contains: paths, schema, config, quality gates, registry status    │
│  Backend agnostic: works with S3, local filesystem, or SQLite       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│               LAYER 3: LOCAL ORCHESTRATOR / RUNNER                  │
│  Prefect / Metaflow / Custom Python runner                          │
│  Executes the DAG: data → features → train → eval → registry       │
│  Runs locally for dev, scales to cloud for production               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ (imports and calls)
┌────────────────────────────────▼────────────────────────────────────┐
│             LAYER 2: PYTHON MODULES / PACKAGES                      │
│  aiconnex_ml/                                                       │
│  ├── data/       → schema validation, contract checks               │
│  ├── features/   → rolling windows, lag, scaling                    │
│  ├── training/   → unified registry, HPO, GPU detection             │
│  ├── evaluation/ → metrics, residuals, confidence intervals         │
│  ├── explain/    → SHAP, feature importance                         │
│  ├── robustness/ → noise injection, sensor dropout                  │
│  ├── registry/   → versioning, quality gates, approval              │
│  └── utils/      → S3 helpers, manifest I/O, serialization         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ (thin import)
┌────────────────────────────────▼────────────────────────────────────┐
│                LAYER 1: THIN NOTEBOOKS (AUTHORING)                  │
│  Used ONLY for: EDA, visualization, interactive debugging           │
│  Each cell is 3-5 lines: import function, call it, display result   │
│  Zero business logic inside notebooks                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Thin Notebooks (Authoring Surface)

### What changes from today
Today, Notebook 5 contains ~80 lines of inline training logic. In the new architecture, Notebook 5 becomes:

```python
# TODAY (Fat Notebook — all logic inline)
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

models = {
    "RandomForest": RandomForestRegressor(n_estimators=100, ...),
    "XGBoost": XGBRegressor(n_estimators=100, ...)
}

for name, model in models.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_val)
    rmse = np.sqrt(mean_squared_error(y_val, preds))
    # ... 60 more lines of inline code
```

```python
# FUTURE (Thin Notebook — 5 lines)
from aiconnex_ml.training import run_baselines
from aiconnex_ml.utils.manifest import load_manifest

manifest = load_manifest("s3://aiconnex-ml-pipeline/processed/manifest.json")
results = run_baselines(manifest)
results.display()  # Shows comparison table in notebook
```

### Why this matters
- The `run_baselines()` function can be called from a notebook, a CLI script, a SageMaker step, an Airflow task, or a unit test. **Same code, zero duplication.**
- The notebook becomes a disposable visualization layer. If you delete every notebook, your pipeline still works from the CLI.

---

## Layer 2: Python Modules / Packages (The Core Engine)

This is where all the real ML logic lives. It is a standard, installable Python package.

### Proposed Package Structure

```
aiconnex_ml/
│
├── __init__.py
├── config.py                          # Pydantic models for manifest schema validation
│
├── data/
│   ├── __init__.py
│   ├── contract.py                    # Schema enforcement, type checking
│   ├── loader.py                      # S3/local filesystem data loading
│   └── splitter.py                    # Chronological, group, stratified split strategies
│
├── features/
│   ├── __init__.py
│   ├── engineering.py                 # Rolling, lag, interaction features
│   ├── validation.py                  # Leakage, drift (PSI), collinearity checks
│   └── scaling.py                     # Train-only fit, transform all splits
│
├── training/
│   ├── __init__.py
│   ├── registry.py                    # REGRESSION_REGISTRY, ANOMALY_REGISTRY dicts
│   ├── baselines.py                   # Run all candidate baselines, rank by metric
│   ├── hpo.py                         # RandomizedSearchCV with dynamic GPU detection
│   └── hardware.py                    # GPU/CPU detection, thread management
│
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py                     # R2, RMSE, MAE, MAPE, MaxError, confidence intervals
│   ├── plots.py                       # Predicted vs. actual, residuals, distributions
│   └── segments.py                    # Per-engine / per-segment performance breakdown
│
├── explain/
│   ├── __init__.py
│   ├── shap_analysis.py               # TreeExplainer, global importance, beeswarm
│   └── report.py                      # JSON report generation
│
├── robustness/
│   ├── __init__.py
│   ├── noise.py                       # Gaussian noise injection at varying sigma
│   ├── dropout.py                     # Sensor failure simulation
│   └── report.py                      # Stability pass/fail determination
│
├── registry_commit/
│   ├── __init__.py
│   ├── gates.py                       # Quality gate checks (RMSE < threshold, etc.)
│   ├── versioning.py                  # Semantic versioning, S3 folder management
│   └── approval.py                    # Write DEPLOYMENT_READY flag to manifest
│
└── utils/
    ├── __init__.py
    ├── manifest.py                    # load_manifest(), save_manifest(), merge operations
    ├── s3.py                          # S3 upload/download helpers
    ├── serialization.py               # Pickle, ONNX, Treelite export
    └── compatibility.py               # numpy type casting, version-safe metric wrappers
```

### Key Design Principles

#### Principle 1: Every function is manifest-driven
```python
# aiconnex_ml/training/baselines.py

def run_baselines(manifest: dict) -> dict:
    """Trains all candidate algorithms defined in the manifest and returns ranked results."""
    
    candidates = manifest["config"].get("candidate_algorithms", ["XGBoost", "RandomForest"])
    feature_cols = manifest["schema"]["final_features"]
    target_col = manifest["schema"]["target_column"]
    
    # Load data from manifest paths
    X_train, y_train = _load_split(manifest["paths"]["train_engineered"], feature_cols, target_col)
    X_val, y_val = _load_split(manifest["paths"]["val_engineered"], feature_cols, target_col)
    
    # Train each candidate from the registry
    results = []
    for algo_name in candidates:
        spec = REGRESSION_REGISTRY[algo_name]
        model = spec["class"]()
        model.fit(X_train, y_train)
        rmse = np.sqrt(mean_squared_error(y_val, model.predict(X_val)))
        results.append({"algorithm": algo_name, "rmse": rmse, "model": model})
    
    return sorted(results, key=lambda x: x["rmse"])
```

#### Principle 2: Every function is independently testable
```python
# tests/test_baselines.py

def test_run_baselines_returns_sorted_results():
    mock_manifest = {
        "config": {"candidate_algorithms": ["Ridge", "LinearRegression"]},
        "schema": {"final_features": ["f1", "f2"], "target_column": "target"},
        "paths": {"train_engineered": "tests/fixtures/train.parquet",
                  "val_engineered": "tests/fixtures/val.parquet"}
    }
    results = run_baselines(mock_manifest)
    assert results[0]["rmse"] <= results[1]["rmse"]  # Verify sorted order
```

#### Principle 3: Version-safe wrappers eliminate runtime crashes
```python
# aiconnex_ml/utils/compatibility.py

import numpy as np
from sklearn.metrics import mean_squared_error

def safe_rmse(y_true, y_pred) -> float:
    """Compute RMSE in a way that works across ALL scikit-learn versions."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))

def safe_json_serialize(obj) -> object:
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj
```

---

## Layer 3: Local Orchestrator / Runner

### Option A: Custom Python Runner (Simplest, No Dependencies)
A lightweight Python script that imports and runs each step sequentially. No external framework needed.

```python
# runner.py — The entire orchestrator in 40 lines

from aiconnex_ml.utils.manifest import load_manifest, save_manifest
from aiconnex_ml.data.contract import validate_contract
from aiconnex_ml.data.splitter import split_data
from aiconnex_ml.features.engineering import engineer_features
from aiconnex_ml.features.validation import validate_features
from aiconnex_ml.training.baselines import run_baselines
from aiconnex_ml.training.hpo import run_hpo
from aiconnex_ml.evaluation.metrics import evaluate_model
from aiconnex_ml.explain.shap_analysis import explain_model
from aiconnex_ml.robustness.noise import stress_test
from aiconnex_ml.registry_commit.approval import commit_to_registry

def run_pipeline(manifest_path: str):
    manifest = load_manifest(manifest_path)
    
    steps = [
        ("Data Contract",       validate_contract),
        ("Split",               split_data),
        ("Feature Engineering",  engineer_features),
        ("Feature Validation",   validate_features),
        ("Baseline Training",    run_baselines),
        ("HPO Tuning",          run_hpo),
        ("Model Evaluation",     evaluate_model),
        ("Explainability",       explain_model),
        ("Robustness Testing",   stress_test),
        ("Registry Commit",      commit_to_registry),
    ]
    
    for step_name, step_fn in steps:
        print(f"{'='*60}")
        print(f"  STEP: {step_name}")
        print(f"{'='*60}")
        manifest = step_fn(manifest)
        save_manifest(manifest, manifest_path)
        print(f"  ✅ {step_name} completed.\n")

if __name__ == "__main__":
    run_pipeline("s3://aiconnex-ml-pipeline/processed/manifest.json")
```

### Option B: Prefect (Production-Grade, Scales to Cloud)
If you need retries, scheduling, monitoring dashboards, and cloud scaling:

```python
# prefect_pipeline.py

from prefect import flow, task
from aiconnex_ml.training.baselines import run_baselines
from aiconnex_ml.training.hpo import run_hpo
# ... other imports

@task(retries=2, retry_delay_seconds=30)
def train_baselines(manifest):
    return run_baselines(manifest)

@task(retries=1)
def tune_hyperparameters(manifest):
    return run_hpo(manifest)

@flow(name="CMAPSS-Regression-Pipeline")
def regression_pipeline(manifest_path: str):
    manifest = load_manifest(manifest_path)
    manifest = validate_contract(manifest)
    manifest = split_data(manifest)
    manifest = engineer_features(manifest)
    manifest = validate_features(manifest)
    manifest = train_baselines(manifest)
    manifest = tune_hyperparameters(manifest)
    manifest = evaluate_model(manifest)
    manifest = explain_model(manifest)
    manifest = stress_test(manifest)
    manifest = commit_to_registry(manifest)
```

### Option C: Metaflow (ML-Specific, Netflix-Built)
If the team is data-scientist-heavy and needs experiment versioning baked in:

```python
# metaflow_pipeline.py

from metaflow import FlowSpec, step
from aiconnex_ml.training.baselines import run_baselines

class RegressionPipeline(FlowSpec):
    
    @step
    def start(self):
        self.manifest = load_manifest(self.manifest_path)
        self.next(self.train_baselines)
    
    @step
    def train_baselines(self):
        self.results = run_baselines(self.manifest)
        self.next(self.tune)
    
    @step
    def tune(self):
        self.manifest = run_hpo(self.manifest)
        self.next(self.end)
    
    @step
    def end(self):
        print("Pipeline complete.")
```

### Comparison for Your Use Case

| Factor | Custom Runner | Prefect | Metaflow |
|:-------|:-------------|:--------|:---------|
| **Setup Complexity** | Zero. Pure Python. | `pip install prefect`. Moderate. | `pip install metaflow`. Moderate. |
| **Local Dev Speed** | Instant. Just `python runner.py`. | Fast. `prefect deploy` for cloud. | Fast. `python flow.py run`. |
| **Retry/Fault Tolerance** | Manual (try/except). | Built-in `retries`, `retry_delay`. | Built-in `@retry`. |
| **Cloud Scaling** | Manual Docker/K8s setup. | Native Kubernetes/ECS/Lambda support. | Native AWS Batch/K8s support. |
| **Monitoring Dashboard** | None (print logs). | Prefect UI (self-hosted or cloud). | Metaflow UI (self-hosted). |
| **Edge Deployment** | Excellent. No dependencies. | Good. Hybrid model supports edge. | Good. Portable execution. |
| **Best For** | Early-stage, lean teams. | Production teams needing observability. | ML-heavy teams needing experiment tracking. |

> [!IMPORTANT]
> **Recommendation:** Start with the **Custom Python Runner** (Option A). It has zero external dependencies, runs anywhere, and the `aiconnex_ml` package code is identical regardless of which orchestrator you choose later. When you need dashboards or retry logic, wrap the same functions with Prefect decorators. Zero code rewrite.

---

## Layer 4: Portable Manifest Backend

The manifest is the single source of truth. It must work identically whether stored on S3, local disk, or a database.

```python
# aiconnex_ml/utils/manifest.py

import json
import os
import boto3

def load_manifest(path: str) -> dict:
    """Load manifest from S3 or local filesystem."""
    if path.startswith("s3://"):
        from urllib.parse import urlparse
        parsed = urlparse(path)
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))
        return json.loads(obj["Body"].read().decode("utf-8"))
    else:
        with open(path, "r") as f:
            return json.load(f)

def save_manifest(manifest: dict, path: str):
    """Save manifest to S3 or local filesystem."""
    from aiconnex_ml.utils.compatibility import safe_json_serialize
    
    serialized = json.dumps(manifest, indent=2, default=safe_json_serialize)
    
    if path.startswith("s3://"):
        from urllib.parse import urlparse
        parsed = urlparse(path)
        s3 = boto3.client("s3")
        s3.put_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"), Body=serialized)
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(serialized)
```

This means:
- **In Colab:** `load_manifest("s3://aiconnex-ml-pipeline/processed/manifest.json")`
- **On Edge PC:** `load_manifest("/opt/models/manifest.json")`
- **In SageMaker:** `load_manifest("/opt/ml/processing/input/manifest.json")`

Same function. Same code. Zero changes.

---

## Layer 5: Containerized Edge Execution

### Training Container (Heavy — Runs on GPU Server or Cloud)

```dockerfile
# Dockerfile.train
FROM python:3.12-slim

WORKDIR /app
COPY aiconnex_ml/ ./aiconnex_ml/
COPY runner.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "runner.py"]
```

### Inference Container (Lightweight — Runs on Edge Device)

```dockerfile
# Dockerfile.inference
FROM python:3.12-slim

WORKDIR /app
COPY aiconnex_ml/utils/ ./aiconnex_ml/utils/
COPY inference_server.py .
COPY requirements-inference.txt .

# Only install inference-time dependencies (no sklearn, no shap, no matplotlib)
RUN pip install --no-cache-dir -r requirements-inference.txt

EXPOSE 8080
ENTRYPOINT ["uvicorn", "inference_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Inference Server (FastAPI — 30 Lines)

```python
# inference_server.py
from fastapi import FastAPI
import pickle
import numpy as np
import json

app = FastAPI()

# Load model and manifest at startup
with open("/opt/models/best_model.pkl", "rb") as f:
    model = pickle.load(f)
with open("/opt/models/manifest.json", "r") as f:
    manifest = json.load(f)

feature_cols = manifest["schema"]["final_features"]

@app.post("/predict")
async def predict(data: dict):
    # Reorder features to match training order
    features = np.array([[data[col] for col in feature_cols]])
    prediction = model.predict(features)
    return {"prediction": float(prediction[0])}
```

---

## Layer 6: Optional Cloud Sync / Control Plane

This layer is only activated when you need remote visibility, experiment tracking, or model comparison dashboards.

| Tool | Purpose | When to Activate |
|:-----|:--------|:-----------------|
| **S3** | Artifact storage (models, reports, plots) | Always (already in use) |
| **MLflow** | Experiment tracking, model registry, metric comparison | When running multiple experiments or comparing model versions |
| **DVC (Data Version Control)** | Version datasets alongside code in Git | When datasets change frequently and you need reproducibility |
| **Prometheus + Grafana** | Monitor inference latency, throughput, drift on edge | When model is deployed to production edge devices |

---

## How This Maps to SORBA's Architecture

Based on research, SORBA internally follows a very similar pattern:

| SORBA Component | Our Equivalent |
|:---------------|:---------------|
| Auto-ETL connectors (60+ data sources) | Phase 1 data ingestion (out of scope for Phase 2) |
| 4-click wizard UI | Node.js DAG frontend → writes manifest config |
| AutoML Studio (automated algorithm selection) | `REGRESSION_REGISTRY` + `ANOMALY_REGISTRY` dictionaries |
| Template-based approach (10+ app templates) | Manifest-driven config: `"ml_task": "regression"` or `"anomaly"` |
| Edge-to-Cloud deployment | Docker containers: heavy (training), lightweight (inference) |
| Real-time monitoring | Prometheus + Grafana on edge, optional cloud dashboard |

The critical difference: **SORBA is a closed-source, vendor-locked platform.** Our architecture achieves the same capabilities with open-source, portable components that you own and control.

---

## Migration Path (From Current Notebooks to This Architecture)

> [!IMPORTANT]
> This is not a rewrite. It is a structured extraction.

| Phase | What Happens | Effort |
|:------|:------------|:-------|
| **Phase A** | Extract all inline functions from notebooks into `aiconnex_ml/` Python modules. Notebooks become thin wrappers that import and call. | 2-3 days |
| **Phase B** | Write unit tests for each module. Pin all library versions in `requirements.txt`. | 1-2 days |
| **Phase C** | Create `runner.py` (custom orchestrator). Verify full pipeline runs end-to-end from CLI. | 1 day |
| **Phase D** | Dockerize the training pipeline. Test locally with `docker run`. | 1 day |
| **Phase E** | Create lightweight inference container. Deploy to edge test device. | 1 day |
| **Phase F** | (Optional) Add Prefect decorators for production monitoring and retry logic. | 1 day |
