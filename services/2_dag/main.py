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
        "results": run.results,
        
        # Expose file paths directly
        "raw_file_path": getattr(run, "raw_file_path", None),
        "prepared_file_path": getattr(run, "prepared_file_path", None),
        "engineered_file_path": getattr(run, "engineered_file_path", None),
        "train_path": getattr(run, "train_path", None),
        "val_path": getattr(run, "val_path", None),
        "test_path": getattr(run, "test_path", None),
        "model_path": getattr(run, "model_path", None),
        "scaler_path": getattr(run, "scaler_path", None),
        "manifest_path": getattr(run, "manifest_path", None)
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

if __name__ == "__main__":
    import uvicorn
    should_reload = os.environ.get("AIC_RELOAD", "0").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=should_reload)
