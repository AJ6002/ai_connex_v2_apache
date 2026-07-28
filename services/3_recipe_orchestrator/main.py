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

class SaveRecipePayload(BaseModel):
    category: str  # 'preparing', 'feature_engineering', 'training', 'splitting'
    dag_id: str
    content: Dict[str, Any]

class DeleteRecipePayload(BaseModel):
    category: str
    dag_id: str

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "Recipe Orchestrator API"}

@app.get("/api/v1/recipes/all")
def get_all_recipes():
    base_path = os.path.dirname(__file__)
    categories = ['preparing', 'feature_engineering', 'splitting', 'training']
    result = {}
    for cat in categories:
        cat_dir = os.path.join(base_path, "recipe", cat)
        result[cat] = {}
        if os.path.exists(cat_dir):
            for fname in os.listdir(cat_dir):
                if fname.endswith(".json"):
                    dag_key = fname.replace(".json", "")
                    try:
                        with open(os.path.join(cat_dir, fname), 'r', encoding='utf-8') as f:
                            result[cat][dag_key] = json.load(f)
                    except Exception:
                        pass
    return {"status": "success", "recipes": result}

@app.post("/api/v1/recipes/save")
def save_recipe(payload: SaveRecipePayload):
    try:
        base_path = os.path.dirname(__file__)
        cat_dir = os.path.join(base_path, "recipe", payload.category)
        os.makedirs(cat_dir, exist_ok=True)
        file_path = os.path.join(cat_dir, f"{payload.dag_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload.content, f, indent=2)
        return {"status": "success", "message": f"Recipe {payload.dag_id} saved under {payload.category}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/recipes/delete")
def delete_recipe(payload: DeleteRecipePayload):
    try:
        base_path = os.path.dirname(__file__)
        file_path = os.path.join(base_path, "recipe", payload.category, f"{payload.dag_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"status": "success", "message": f"Recipe {payload.dag_id} deleted."}
        else:
            raise HTTPException(status_code=404, detail="Recipe file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            fallback_id = "DAG_283"
        elif "Anomaly" in task_str:
            fallback_id = "DAG_573"
        elif "Clustering" in task_str:
            fallback_id = "DAG_820"
        elif "Time" in task_str:
            fallback_id = "DAG_1059"
        elif "Twin" in task_str:
            fallback_id = "DAG_1316"
        elif "Reinforcement" in task_str:
            fallback_id = "DAG_1451"
        elif "Recommend" in task_str:
            fallback_id = "DAG_1572"
        elif "nlp" in task_str.lower() or "text" in task_str.lower():
            fallback_id = "DAG_1705"
        elif "vision" in task_str.lower() or "image" in task_str.lower():
            fallback_id = "DAG_1837"
            
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(base_dir, "Documentation", "transit_mappings", "algorithm_dags_transit_mapping.json")
        
        # Load from central JSON database
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail=f"Database file not found at: {db_path}")
            
        with open(db_path, "r", encoding="utf-8") as f:
            json_db = json.load(f)
            
        if dag_id not in json_db:
            # Fallback
            dag_id = fallback_id
            if dag_id not in json_db:
                # Default fallback
                dag_id = "DAG_001"
                
        dag_info = json_db[dag_id]
        recipes = dag_info["recipes"]
        
        # Deep copy to prevent mutating the shared database in memory
        prep_recipe = dict(recipes["prepare_recipe"])
        feat_recipe = dict(recipes["feature_engineering_recipe"])
        split_recipe = dict(recipes["splitting_recipe"])
        train_recipe = dict(recipes["training_recipe"])
        
        # 3. Merge user overrides from meta2
        # Preparing overrides
        for k in ["impute_strategy", "scale_method", "categorical_encoding", "outlier_method"]:
            if k in meta2:
                prep_recipe[k] = meta2[k]
                
        # Feature Engineering overrides
        for k in ["polynomial_degree", "interaction_features", "pca_components", "feature_selection_method", "k_best_features"]:
            if k in meta2:
                feat_recipe[k] = meta2[k]
                
        # Splitting overrides
        for k in ["split_method", "test_size", "random_state"]:
            if k in meta2:
                split_recipe[k] = meta2[k]
                
        # Training overrides
        for k in ["algorithm", "variant", "use_gpu", "early_stopping", "class_weight", "hyperparameters"]:
            if k in meta2:
                train_recipe[k] = meta2[k]
                
        # 4. Save resolved runtime recipe combination to meta/meta3.json
        meta3_dir = os.path.join(os.path.dirname(__file__), "meta")
        os.makedirs(meta3_dir, exist_ok=True)
        meta3_path = os.path.join(meta3_dir, "meta3.json")
        
        meta3_payload = {
            "dag_id": dag_id,
            "suggested_task": suggested_task,
            "resolved_at": str(os.path.getmtime(db_path)),
            "recipe_sources": {
                "database": db_path
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


# ─────────────────────────────────────────────────────────────────────────────
# Per-Service Recipe CRUD (reads/writes the ACTUAL service recipe folders)
# These are the canonical recipe files used by 4_prepare, 5_FE, 6_split, 7_train
# ─────────────────────────────────────────────────────────────────────────────

SERVICE_RECIPE_DIRS = {
    "preparing":           os.path.join(os.path.dirname(__file__), "..", "4_prepare", "recipe"),
    "feature_engineering": os.path.join(os.path.dirname(__file__), "..", "5_feature_engineering", "recipe"),
    "splitting":           os.path.join(os.path.dirname(__file__), "..", "6_split", "recipe"),
    "training":            os.path.join(os.path.dirname(__file__), "..", "7_train", "recipe"),
    "evaluating":          os.path.join(os.path.dirname(__file__), "..", "8_evaluate", "recipe"),
}

# Also mirror to the orchestrator's own recipe folders so orchestrate() still works
ORCH_RECIPE_DIRS = {
    "preparing":           os.path.join(os.path.dirname(__file__), "recipe", "preparing"),
    "feature_engineering": os.path.join(os.path.dirname(__file__), "recipe", "feature_engineering"),
    "splitting":           os.path.join(os.path.dirname(__file__), "recipe", "splitting"),
    "training":            os.path.join(os.path.dirname(__file__), "recipe", "training"),
}

@app.get("/api/v1/service-recipes/all")
def get_service_recipes_all():
    """Return all recipes from the actual per-service recipe folders."""
    result = {}
    for cat, dir_path in SERVICE_RECIPE_DIRS.items():
        result[cat] = {}
        abs_dir = os.path.abspath(dir_path)
        if os.path.exists(abs_dir):
            for fname in sorted(os.listdir(abs_dir)):
                if fname.endswith(".json"):
                    dag_key = fname.replace(".json", "")
                    try:
                        with open(os.path.join(abs_dir, fname), 'r', encoding='utf-8') as f:
                            result[cat][dag_key] = json.load(f)
                    except Exception:
                        pass
    return {"status": "success", "recipes": result}


@app.get("/api/v1/service-recipes/{category}/{dag_id}")
def get_service_recipe(category: str, dag_id: str):
    """Return one recipe from the per-service folder."""
    if category not in SERVICE_RECIPE_DIRS:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")
    dir_path = os.path.abspath(SERVICE_RECIPE_DIRS[category])
    file_path = os.path.join(dir_path, f"{dag_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"{dag_id} not found in {category}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return {"status": "success", "dag_id": dag_id, "category": category, "content": json.load(f)}



def sync_dag_metadata(dag_id: str, content: dict, category: str):
    """
    Automatically updates dag_mapping.json and dag_conditions_mapping.json
    when a recipe is saved/updated in the recipe library.
    """
    try:
        # Deduce family based on dag_id suffix number (e.g., DAG_001 -> 1)
        num_str = "".join([c for c in dag_id if c.isdigit()])
        if not num_str:
            return
        num = int(num_str)
        
        family = "CLASSIFICATION"
        if 1 <= num <= 240:
            family = "CLASSIFICATION"
        elif 241 <= num <= 485:
            family = "REGRESSION"
        elif 486 <= num <= 695:
            family = "ANOMALY DETECTION"
        elif 696 <= num <= 905:
            family = "CLUSTERING"
        elif 906 <= num <= 1130:
            family = "TIME-SERIES"
        elif 1131 <= num <= 1240:
            family = "DIGITAL TWIN"
        elif 1241 <= num <= 1340:
            family = "REINFORCEMENT LEARNING"
        elif 1341 <= num <= 1450:
            family = "RECOMMENDATION"
        elif 1451 <= num <= 1560:
            family = "NLP/TEXT-CLASSIFICATION"
        elif 1561 <= num <= 2500:
            family = "COMPUTER VISION"
        else:
            family = "CLASSIFICATION"
            
        base_dir = os.path.dirname(__file__)
        dag_dir = os.path.abspath(os.path.join(base_dir, "..", "2_dag"))
        
        # 1. Update dag_mapping.json
        mapping_path = os.path.join(dag_dir, "dag_mapping.json")
        if os.path.exists(mapping_path):
            with open(mapping_path, "r", encoding="utf-8") as f:
                mapping = json.load(f)
            
            family_list = mapping.setdefault(family, [])
            exists = False
            for entry in family_list:
                if entry.get("dag_id") == dag_id:
                    if category == "training":
                        entry["algorithm"] = content.get("algorithm", entry.get("algorithm", "Unknown"))
                        entry["variant"] = content.get("variant", entry.get("variant", "Standard"))
                    exists = True
                    break
            if not exists:
                family_list.append({
                    "dag_id": dag_id,
                    "algorithm": content.get("algorithm", "Custom Algorithm") if category == "training" else "Custom Algorithm",
                    "variant": content.get("variant", "Standard") if category == "training" else "Standard"
                })
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2, ensure_ascii=False)
                
        # 2. Update dag_conditions_mapping.json
        conditions_path = os.path.join(dag_dir, "dag_conditions_mapping.json")
        if os.path.exists(conditions_path):
            with open(conditions_path, "r", encoding="utf-8") as f:
                conditions = json.load(f)
            
            entry = conditions.setdefault(dag_id, {
                "dag_id": dag_id,
                "family": family,
                "algorithm": "Custom Algorithm",
                "variant": "Standard",
                "condition": "custom user defined recipe",
                "decision": {
                    "family": family,
                    "algorithm": "Custom Algorithm",
                    "variant": "Standard",
                    "pipeline_actions": {},
                    "special_handling": "None"
                }
            })
            
            if category == "training":
                algo = content.get("algorithm", entry.get("algorithm"))
                var = content.get("variant", entry.get("variant"))
                entry["algorithm"] = algo
                entry["variant"] = var
                entry["decision"]["algorithm"] = algo
                entry["decision"]["variant"] = var
            elif category == "preparing":
                entry["decision"]["pipeline_actions"]["imputation"] = content.get("impute_strategy", "mean")
                entry["decision"]["pipeline_actions"]["scaling"] = content.get("scale_method", "standard")
                entry["decision"]["pipeline_actions"]["encoding"] = content.get("encode_strategy", "one-hot")
                entry["decision"]["pipeline_actions"]["outlier_handling"] = content.get("outlier_method", "none")
            
            with open(conditions_path, "w", encoding="utf-8") as f:
                json.dump(conditions, f, indent=2, ensure_ascii=False)
                
    except Exception as e:
        print(f"Error syncing dag metadata: {e}")


@app.post("/api/v1/service-recipes/save")
def save_service_recipe(payload: SaveRecipePayload):
    """
    Save a recipe to the actual per-service folder AND mirror to the orchestrator folder.
    This means editing via Master Data propagates everywhere the recipe is consumed.
    """
    if payload.category not in SERVICE_RECIPE_DIRS:
        raise HTTPException(status_code=400, detail=f"Unknown category: {payload.category}")
    saved_to = []
    errors = []

    # 1. Write to per-service folder
    svc_dir = os.path.abspath(SERVICE_RECIPE_DIRS[payload.category])
    os.makedirs(svc_dir, exist_ok=True)
    svc_path = os.path.join(svc_dir, f"{payload.dag_id}.json")
    try:
        with open(svc_path, 'w', encoding='utf-8') as f:
            json.dump(payload.content, f, indent=4)
        saved_to.append(svc_path)
    except Exception as e:
        errors.append(f"service folder: {e}")

    # 2. Mirror to orchestrator recipe folder (so orchestrate() picks it up too)
    if payload.category in ORCH_RECIPE_DIRS:
        orch_dir = os.path.abspath(ORCH_RECIPE_DIRS[payload.category])
        os.makedirs(orch_dir, exist_ok=True)
        orch_path = os.path.join(orch_dir, f"{payload.dag_id}.json")
        try:
            with open(orch_path, 'w', encoding='utf-8') as f:
                json.dump(payload.content, f, indent=4)
            saved_to.append(orch_path)
        except Exception as e:
            errors.append(f"orchestrator mirror: {e}")

    # Sync metadata mapping across 2_dag engine database
    sync_dag_metadata(payload.dag_id, payload.content, payload.category)

    if errors:
        raise HTTPException(status_code=500, detail="; ".join(errors))

    return {
        "status": "success",
        "message": f"Recipe {payload.dag_id} saved, synced with DAG engine registry, and mirrored to {len(saved_to)} location(s).",
        "saved_to": saved_to
    }


@app.post("/api/v1/service-recipes/delete")
def delete_service_recipe(payload: DeleteRecipePayload):
    """Delete a recipe from both the per-service folder and the orchestrator mirror."""
    if payload.category not in SERVICE_RECIPE_DIRS:
        raise HTTPException(status_code=400, detail=f"Unknown category: {payload.category}")
    deleted = []

    svc_path = os.path.join(os.path.abspath(SERVICE_RECIPE_DIRS[payload.category]), f"{payload.dag_id}.json")
    if os.path.exists(svc_path):
        os.remove(svc_path)
        deleted.append(svc_path)

    if payload.category in ORCH_RECIPE_DIRS:
        orch_path = os.path.join(os.path.abspath(ORCH_RECIPE_DIRS[payload.category]), f"{payload.dag_id}.json")
        if os.path.exists(orch_path):
            os.remove(orch_path)
            deleted.append(orch_path)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"{payload.dag_id} not found in {payload.category}")

    return {"status": "success", "deleted": deleted}


if __name__ == '__main__':
    import uvicorn
    should_reload = os.environ.get("AIC_RELOAD", "0").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=should_reload)
