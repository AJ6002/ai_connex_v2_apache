from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import json
import glob

app = FastAPI(
    title="Recipe Generator Dashboard API",
    description="External application to edit existing, add new, and delete wasted recipes across all 3 category folders.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # services/
AIC_ROOT = os.path.dirname(BASE_DIR) # aic/
SERVICES_DIR = BASE_DIR
LESS_MAIN_DIR = os.path.join(AIC_ROOT, "less_main")

# Define category folders mapping
CATEGORY_FOLDERS = {
    "prepare": [
        os.path.join(LESS_MAIN_DIR, "prepare", "recipe"),
        os.path.join(SERVICES_DIR, "4_prepare", "recipe"),
        os.path.join(SERVICES_DIR, "3_recipe_orchestrator", "recipe", "preparing")
    ],
    "feature_engineer": [
        os.path.join(LESS_MAIN_DIR, "feature_engineer", "recipe"),
        os.path.join(SERVICES_DIR, "5_feature_engineering", "recipe"),
        os.path.join(SERVICES_DIR, "3_recipe_orchestrator", "recipe", "feature_engineering")
    ],
    "split_train_evaluate": [
        os.path.join(LESS_MAIN_DIR, "split_train_evaluate", "recipe"),
        os.path.join(LESS_MAIN_DIR, "6_split_train_evaluate", "recipe"),
        os.path.join(SERVICES_DIR, "3_recipe_orchestrator", "recipe", "splitting"),
        os.path.join(SERVICES_DIR, "3_recipe_orchestrator", "recipe", "training")
    ]
}

# Ensure base category directories exist
for cat, paths in CATEGORY_FOLDERS.items():
    for p in paths:
        os.makedirs(p, exist_ok=True)

class RecipePayload(BaseModel):
    recipe_id: str
    content: Dict[str, Any]

def resolve_category_key(category: str) -> str:
    cat = category.lower().strip()
    if "prep" in cat:
        return "prepare"
    elif "feature" in cat or "feat" in cat:
        return "feature_engineer"
    elif "split" in cat or "train" in cat or "eval" in cat:
        return "split_train_evaluate"
    elif cat in CATEGORY_FOLDERS:
        return cat
    else:
        raise HTTPException(status_code=400, detail=f"Unknown category '{category}'. Available: {list(CATEGORY_FOLDERS.keys())}")

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "Recipe Generator Dashboard API"}

@app.get("/api/v1/categories")
def get_categories():
    result = {}
    for cat, paths in CATEGORY_FOLDERS.items():
        primary_dir = paths[0]
        files = glob.glob(os.path.join(primary_dir, "*.json"))
        recipe_ids = [os.path.splitext(os.path.basename(f))[0] for f in files]
        result[cat] = {
            "category": cat,
            "primary_folder": primary_dir,
            "folder_count": len(paths),
            "recipe_count": len(files),
            "sample_recipes": recipe_ids[:10]
        }
    return {"status": "success", "categories": result}

@app.get("/api/v1/recipes/{category}")
def list_recipes(category: str):
    cat_key = resolve_category_key(category)
    primary_dir = CATEGORY_FOLDERS[cat_key][0]
    
    files = glob.glob(os.path.join(primary_dir, "*.json"))
    recipes = []
    
    for fpath in sorted(files):
        recipe_id = os.path.splitext(os.path.basename(fpath))[0]
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = json.load(f)
            stat = os.stat(fpath)
            recipes.append({
                "recipe_id": recipe_id,
                "filename": os.path.basename(fpath),
                "modified_at": stat.st_mtime,
                "size_bytes": stat.st_size,
                "content": content
            })
        except Exception as e:
            recipes.append({
                "recipe_id": recipe_id,
                "filename": os.path.basename(fpath),
                "error": str(e)
            })
            
    return {
        "status": "success",
        "category": cat_key,
        "total_count": len(recipes),
        "recipes": recipes
    }

@app.get("/api/v1/recipes/{category}/{recipe_id}")
def get_recipe(category: str, recipe_id: str):
    cat_key = resolve_category_key(category)
    recipe_name = recipe_id if recipe_id.endswith(".json") else f"{recipe_id}.json"
    
    found_path = None
    for p in CATEGORY_FOLDERS[cat_key]:
        candidate = os.path.join(p, recipe_name)
        if os.path.exists(candidate):
            found_path = candidate
            break
            
    if not found_path:
        raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found in category '{cat_key}'")
        
    with open(found_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
        
    return {
        "status": "success",
        "category": cat_key,
        "recipe_id": recipe_id,
        "filepath": found_path,
        "content": content
    }

@app.post("/api/v1/recipes/{category}")
def create_recipe(category: str, payload: RecipePayload):
    cat_key = resolve_category_key(category)
    recipe_id = payload.recipe_id.strip()
    if not recipe_id:
        raise HTTPException(status_code=400, detail="Recipe ID cannot be empty.")
        
    filename = recipe_id if recipe_id.endswith(".json") else f"{recipe_id}.json"
    
    saved_paths = []
    for folder in CATEGORY_FOLDERS[cat_key]:
        os.makedirs(folder, exist_ok=True)
        target = os.path.join(folder, filename)
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(payload.content, f, indent=4)
        saved_paths.append(target)
        
    return {
        "status": "success",
        "message": f"New recipe '{recipe_id}' created across {len(saved_paths)} locations.",
        "category": cat_key,
        "recipe_id": recipe_id,
        "saved_paths": saved_paths,
        "content": payload.content
    }

@app.put("/api/v1/recipes/{category}/{recipe_id}")
def update_recipe(category: str, recipe_id: str, payload: RecipePayload):
    cat_key = resolve_category_key(category)
    filename = recipe_id if recipe_id.endswith(".json") else f"{recipe_id}.json"
    
    updated_paths = []
    for folder in CATEGORY_FOLDERS[cat_key]:
        target = os.path.join(folder, filename)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(payload.content, f, indent=4)
        updated_paths.append(target)
        
    return {
        "status": "success",
        "message": f"Recipe '{recipe_id}' updated successfully.",
        "category": cat_key,
        "recipe_id": recipe_id,
        "updated_paths": updated_paths,
        "content": payload.content
    }

@app.delete("/api/v1/recipes/{category}/{recipe_id}")
def delete_recipe(category: str, recipe_id: str):
    cat_key = resolve_category_key(category)
    filename = recipe_id if recipe_id.endswith(".json") else f"{recipe_id}.json"
    
    deleted_paths = []
    for folder in CATEGORY_FOLDERS[cat_key]:
        target = os.path.join(folder, filename)
        if os.path.exists(target):
            try:
                os.remove(target)
                deleted_paths.append(target)
            except Exception as e:
                print(f"Could not remove {target}: {e}")
                
    if not deleted_paths:
        raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found to delete in '{cat_key}'")
        
    return {
        "status": "success",
        "message": f"Wasted recipe '{recipe_id}' deleted from {len(deleted_paths)} locations.",
        "category": cat_key,
        "recipe_id": recipe_id,
        "deleted_paths": deleted_paths
    }

@app.get("/api/v1/meta/appended")
def get_meta_appended():
    workspace_data = os.path.join(BASE_DIR, "workspace_data")
    master_file = os.path.join(workspace_data, "meta_appended.json")
    
    logs = []
    if os.path.exists(master_file):
        try:
            with open(master_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    # Also inspect individual meta files
    meta1_file = os.path.join(BASE_DIR, "1_dataset_profiler", "meta", "meta1.json")
    meta2_file = os.path.join(BASE_DIR, "2_dag", "meta", "meta2.json")
    meta3_file = os.path.join(BASE_DIR, "3_recipe_orchestrator", "meta", "meta3.json")
    
    meta_summaries = {}
    for name, fpath in [("meta1", meta1_file), ("meta2", meta2_file), ("meta3", meta3_file)]:
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                meta_summaries[name] = {
                    "last_updated": data.get("_last_updated", "N/A"),
                    "history_count": len(data.get("history", [])) if "history" in data else 1,
                    "latest": data
                }
            except Exception as e:
                meta_summaries[name] = {"error": str(e)}
        else:
            meta_summaries[name] = {"status": "Not yet generated"}
            
    return {
        "status": "success",
        "total_appended_events": len(logs),
        "appended_stream": logs,
        "meta_files": meta_summaries
    }

# Static Dashboard Frontend Mounting
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Recipe Generator Dashboard API running. Access /static/index.html or /api/v1/categories"}

if __name__ == "__main__":
    import uvicorn
    print("Starting Recipe Generator Dashboard App on http://127.0.0.1:8009...")
    uvicorn.run(app, host="127.0.0.1", port=8009)
