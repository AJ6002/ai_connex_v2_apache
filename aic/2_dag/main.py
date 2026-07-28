from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import json

from orchestrator import create_pipeline_run, RUNS

app = FastAPI(
    title="Pipeline Orchestrator Engine",
    description="Orchestrates 6-step DAG executions (Prepare -> Feature Eng -> Split -> Train -> Eval -> Deploy).",
    version="1.0.0"
)

# Enable CORS for frontend dashboard communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProfilePayload(BaseModel):
    profile: Dict[str, Any]

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "Pipeline Engine API"}

@app.post("/api/v1/pipeline/run")
async def start_pipeline(payload: Dict[str, Any]):
    profile = payload.get("profile", payload)
    
    if not profile or "algorithm_family" not in profile:
        raise HTTPException(
            status_code=400,
            detail="Invalid payload. Profile must contain 'algorithm_family'."
        )
        
    try:
        run = create_pipeline_run(profile)
        return {
            "status": "success",
            "dag_id": run.run_id,
            "algorithm_family": run.algorithm_family,
            "pipeline_status": run.status,
            "message": "Pipeline execution started in the background."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start pipeline: {str(e)}"
        )

@app.get("/api/v1/pipeline/{dag_id}/status")
def get_pipeline_status(dag_id: str):
    if dag_id not in RUNS:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline run '{dag_id}' not found."
        )
        
    run = RUNS[dag_id]
    return {
        "dag_id": run.dag_id,
        "algorithm_family": run.algorithm_family,
        "status": run.status,
        "progress_pct": run.progress_pct,
        "current_step": run.current_step,
        "steps": run.steps,
        "logs": run.logs,
        "results": run.results
    }

@app.get("/api/v1/plots/dag_tree/{dag_id}")
def get_dag_tree_plot(dag_id: str):
    try:
        base_dir = os.path.dirname(__file__)
        mapping_path = os.path.join(base_dir, "dag_conditions_mapping.json")
        
        node_info = {}
        if os.path.exists(mapping_path):
            with open(mapping_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if dag_id in data:
                    node_info = data[dag_id]

        family = node_info.get("family", "CLASSIFICATION")
        algo = node_info.get("algorithm", "Logistic Regression")
        variant = node_info.get("variant", "Standard")
        condition = node_info.get("condition", "Dataset conditions satisfied")
        
        # Build DAG decision tree nodes
        nodes = [
            {"id": "node_input", "label": "Raw Tabular Dataset", "type": "input", "group": "input"},
            {"id": "node_eval", "label": f"Condition Evaluator\n({condition})", "type": "decision", "group": "logic"},
            {"id": "node_dag", "label": f"Recommended DAG\n[{dag_id}]", "type": "dag", "group": "dag"},
            {"id": "node_prep", "label": "Step 1: PREPARE\n(Impute, Scale, Encode)", "type": "step", "group": "step"},
            {"id": "node_feat", "label": "Step 2: FEATURE ENG\n(Poly, PCA, Select)", "type": "step", "group": "step"},
            {"id": "node_split", "label": "Step 3: SPLIT\n(Train / Val / Test)", "type": "step", "group": "step"},
            {"id": "node_train", "label": f"Step 4: TRAIN\n({algo} - {variant})", "type": "step", "group": "step"},
            {"id": "node_eval_step", "label": "Step 5: EVAL\n(Validation Metrics)", "type": "step", "group": "step"},
            {"id": "node_deploy", "label": "Step 6: DEPLOY\n(API Endpoint)", "type": "step", "group": "step"}
        ]
        
        edges = [
            {"from": "node_input", "to": "node_eval"},
            {"from": "node_eval", "to": "node_dag"},
            {"from": "node_dag", "to": "node_prep"},
            {"from": "node_prep", "to": "node_feat"},
            {"from": "node_feat", "to": "node_split"},
            {"from": "node_split", "to": "node_train"},
            {"from": "node_train", "to": "node_eval_step"},
            {"from": "node_eval_step", "to": "node_deploy"}
        ]

        return {
            "dag_id": dag_id,
            "family": family,
            "algorithm": algo,
            "variant": variant,
            "condition": condition,
            "tree": {
                "nodes": nodes,
                "edges": edges
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/plots/execution_timeline/{run_id}")
def get_execution_timeline_plot(run_id: str):
    if run_id not in RUNS:
        # Generate sample timeline if run not found
        return {
            "run_id": run_id,
            "timeline": [
                {"step": "PREPARE", "duration_sec": 1.8, "status": "completed"},
                {"step": "FEATURE_ENG", "duration_sec": 2.2, "status": "completed"},
                {"step": "SPLIT", "duration_sec": 0.8, "status": "completed"},
                {"step": "TRAIN", "duration_sec": 3.4, "status": "completed"},
                {"step": "EVAL", "duration_sec": 1.5, "status": "completed"},
                {"step": "DEPLOY", "duration_sec": 1.1, "status": "completed"}
            ]
        }
    run = RUNS[run_id]
    timeline = []
    for s in run.steps:
        timeline.append({
            "step": s["name"].split(" (")[0],
            "duration_sec": s.get("duration", 2.0),
            "status": s.get("status", "completed")
        })
    return {"run_id": run_id, "timeline": timeline}

@app.api_route("/api/v1/predict/{run_id}", methods=["GET", "POST"])
async def predict_endpoint(run_id: str, payload: Optional[Dict[str, Any]] = None):
    """Serving REST prediction endpoint for deployed models."""
    # 1. Resolve model file path
    workspace_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspace_data")
    model_path = None
    scaler_path = None

    # Search for model_run_<run_id>.pkl or deployed model matching run_id
    if run_id in RUNS:
        run = RUNS[run_id]
        if hasattr(run, "model_path") and run.model_path and os.path.exists(run.model_path):
            model_path = run.model_path
            scaler_path = getattr(run, "scaler_path", None)

    if not model_path or not os.path.exists(model_path):
        for root, dirs, files in os.walk(workspace_root):
            for f in files:
                if f.endswith(".pkl") and run_id in f and "scaler" not in f:
                    model_path = os.path.join(root, f)
                    sc_cand = os.path.join(root, f.replace("model_", "scaler_"))
                    if os.path.exists(sc_cand):
                        scaler_path = sc_cand
                    break
            if model_path:
                break

    if not model_path or not os.path.exists(model_path):
        raise HTTPException(
            status_code=404,
            detail=f"Deployed model for run_id '{run_id}' not found."
        )

    # 2. GET request → Return active endpoint status & instructions
    if payload is None:
        return {
            "status": "active",
            "service": "AIConnex Model Prediction API",
            "run_id": run_id,
            "model_path": model_path,
            "has_scaler": bool(scaler_path and os.path.exists(scaler_path)),
            "usage": "POST JSON payload with {'features': [val1, val2, ...]} or {'features': {'col1': val1, ...}}"
        }

    # 3. POST request → Execute model inference
    try:
        import pickle
        import pandas as pd
        import numpy as np

        with open(model_path, "rb") as f:
            model = pickle.load(f)

        features = payload.get("features", payload)
        if isinstance(features, dict):
            df_in = pd.DataFrame([features])
        elif isinstance(features, list):
            if len(features) > 0 and isinstance(features[0], list):
                df_in = pd.DataFrame(features)
            else:
                df_in = pd.DataFrame([features])
        else:
            raise ValueError("Payload features must be a dict or list of numbers.")

        # Scaler transformation if available
        if scaler_path and os.path.exists(scaler_path):
            try:
                with open(scaler_path, "rb") as f:
                    scaler = pickle.load(f)
                if hasattr(scaler, "transform") and df_in.shape[1] == getattr(scaler, "n_features_in_", df_in.shape[1]):
                    df_in = scaler.transform(df_in)
            except Exception:
                pass

        # Model prediction
        if hasattr(model, "predict"):
            preds = model.predict(df_in)
            if hasattr(preds, "tolist"):
                preds = preds.tolist()
        else:
            raise ValueError("Loaded model object lacks predict() method.")

        return {
            "status": "success",
            "run_id": run_id,
            "predictions": preds,
            "sample_count": len(preds)
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction inference failed: {str(exc)}"
        )

if __name__ == "__main__":
    import uvicorn
    should_reload = os.environ.get("AIC_RELOAD", "0").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=should_reload)
