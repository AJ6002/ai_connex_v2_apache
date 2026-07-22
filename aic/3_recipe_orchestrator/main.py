from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import os
import json

app = FastAPI(
    title="Recipe Orchestrator API",
    description="Loads and resolves separate Preparing, Feature Engineering, Splitting, and Training recipes based on Recommended DAG IDs.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrchestrationPayload(BaseModel):
    meta1: Dict[str, Any]
    meta2: Dict[str, Any]

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "Recipe Orchestrator API"}

@app.post("/api/v1/orchestrate")
def orchestrate_recipes(payload: OrchestrationPayload):
    try:
        meta1 = payload.meta1
        meta2 = payload.meta2
        
        # 1. Resolve dag_id from metadata
        profile = meta1.get("profile", meta1)
        dag_id = meta2.get("dag_id", profile.get("recommended_dag_id", "DAG_001"))
        suggested_task = meta2.get("suggested_task", profile.get("suggested_task", "Classification"))
        
        # 2. Map task to recipe defaults if needed
        task_str = str(suggested_task)
        fallback_id = "DAG_001"
        
        if "Regression" in task_str:
            fallback_id = "DAG_241"
        elif "Anomaly" in task_str:
            fallback_id = "DAG_486"
        elif "Clustering" in task_str:
            fallback_id = "DAG_696"
        elif "Time" in task_str:
            fallback_id = "DAG_906"
        elif "Twin" in task_str:
            fallback_id = "DAG_1131"
        elif "Reinforcement" in task_str:
            fallback_id = "DAG_1241"
        elif "Recommend" in task_str:
            fallback_id = "DAG_1341"
        elif "nlp" in task_str.lower() or "text" in task_str.lower():
            fallback_id = "DAG_1451"
        elif "vision" in task_str.lower() or "image" in task_str.lower():
            fallback_id = "DAG_1561"
            
        base_path = os.path.dirname(__file__)
        
        # Paths for the 4 recipe categories
        prep_path = os.path.join(base_path, "recipe", "preparing", f"{dag_id}.json")
        feat_path = os.path.join(base_path, "recipe", "feature_engineering", f"{dag_id}.json")
        split_path = os.path.join(base_path, "recipe", "splitting", f"{dag_id}.json")
        train_path = os.path.join(base_path, "recipe", "training", f"{dag_id}.json")
        
        # Fallback lookups if specific DAG ID file doesn't exist
        if not os.path.exists(prep_path):
            prep_path = os.path.join(base_path, "recipe", "preparing", f"{fallback_id}.json")
        if not os.path.exists(feat_path):
            feat_path = os.path.join(base_path, "recipe", "feature_engineering", f"{fallback_id}.json")
        if not os.path.exists(split_path):
            split_path = os.path.join(base_path, "recipe", "splitting", f"{fallback_id}.json")
        if not os.path.exists(train_path):
            train_path = os.path.join(base_path, "recipe", "training", f"{fallback_id}.json")
            
        # 3. Read recipe contents
        with open(prep_path, 'r', encoding='utf-8') as f:
            prep_recipe = json.load(f)
        with open(feat_path, 'r', encoding='utf-8') as f:
            feat_recipe = json.load(f)
        with open(split_path, 'r', encoding='utf-8') as f:
            split_recipe = json.load(f)
        with open(train_path, 'r', encoding='utf-8') as f:
            train_recipe = json.load(f)
            
        # 4. Save resolved runtime recipe combination to meta/meta3.json
        meta3_dir = os.path.join(base_path, "meta")
        os.makedirs(meta3_dir, exist_ok=True)
        meta3_path = os.path.join(meta3_dir, "meta3.json")
        
        meta3_payload = {
            "dag_id": dag_id,
            "suggested_task": suggested_task,
            "resolved_at": str(os.path.getmtime(prep_path)),
            "recipe_sources": {
                "preparing": prep_path,
                "feature_engineering": feat_path,
                "splitting": split_path,
                "training": train_path
            },
            "recipes": {
                "preparing_recipe": prep_recipe,
                "feature_engineering_recipe": feat_recipe,
                "splitting_recipe": split_recipe,
                "training_recipe": train_recipe
            }
        }
        
        with open(meta3_path, 'w', encoding='utf-8') as f:
            json.dump(meta3_payload, f, indent=2)
            
        return {
            "status": "success",
            "message": "Recipes successfully resolved and compiled.",
            "dag_id": dag_id,
            "meta3": meta3_payload
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Orchestration resolution error: {str(e)}"
        )

@app.get("/api/v1/plots/recipe_radar/{dag_id}")
def get_recipe_radar_plot(dag_id: str):
    try:
        base_path = os.path.dirname(__file__)
        prep_p = os.path.join(base_path, "recipe", "preparing", f"{dag_id}.json")
        feat_p = os.path.join(base_path, "recipe", "feature_engineering", f"{dag_id}.json")
        split_p = os.path.join(base_path, "recipe", "splitting", f"{dag_id}.json")
        train_p = os.path.join(base_path, "recipe", "training", f"{dag_id}.json")
        
        if not os.path.exists(prep_p):
            prep_p = os.path.join(base_path, "recipe", "preparing", "DAG_001.json")
            feat_p = os.path.join(base_path, "recipe", "feature_engineering", "DAG_001.json")
            split_p = os.path.join(base_path, "recipe", "splitting", "DAG_001.json")
            train_p = os.path.join(base_path, "recipe", "training", "DAG_001.json")
            
        with open(prep_p, 'r') as f: prep = json.load(f)
        with open(feat_p, 'r') as f: feat = json.load(f)
        with open(split_p, 'r') as f: split = json.load(f)
        with open(train_p, 'r') as f: train = json.load(f)
        
        # Calculate complexity metrics for radar chart
        prep_score = 40 + (20 if prep.get('outlier_method') != 'none' else 0) + (20 if prep.get('scale_method') != 'none' else 0) + (20 if prep.get('encode_strategy') != 'none' else 0)
        feat_score = 30 + (25 if feat.get('polynomial_degree', 1) > 1 else 0) + (25 if feat.get('pca_components', 0) > 0 else 0) + (20 if feat.get('feature_selection_method') != 'none' else 0)
        split_score = int((1.0 - split.get('test_size', 0.2)) * 100)
        
        algo = str(train.get('algorithm', '')).lower()
        if 'boost' in algo or 'xgb' in algo or 'forest' in algo or 'lstm' in algo:
            model_score = 90
        elif 'svm' in algo or 'logistic' in algo or 'ridge' in algo:
            model_score = 70
        else:
            model_score = 55
            
        return {
            "dag_id": dag_id,
            "metrics": [
                {"category": "Data Preparation", "score": min(100, prep_score)},
                {"category": "Feature Engineering", "score": min(100, feat_score)},
                {"category": "Train Data Ratio", "score": min(100, split_score)},
                {"category": "Model Complexity", "score": min(100, model_score)},
                {"category": "Validation Rigor", "score": 85}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    should_reload = os.environ.get("AIC_RELOAD", "0").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=should_reload)
