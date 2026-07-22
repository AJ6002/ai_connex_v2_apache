from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import shutil

# Dynamic root resolution — works on any machine regardless of username or drive
AIC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FINAL_MODEL_DIR = os.path.join(AIC_ROOT, "final_model")
ALGO_FAMILIES_XLSX = os.path.join(AIC_ROOT, "algorithm_families_complete.xlsx")

app = FastAPI(
    title="Model Deployment API",
    description="Deploys finalized model files to the final_model folder and initializes monitoring.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DeployPayload(BaseModel):
    model_path: str
    run_id: str
    dataset_name: str
    dag_id: str

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "Deploy API"}

@app.post("/api/v1/deploy")
def deploy_model(payload: DeployPayload):
    try:
        model_path = payload.model_path
        run_id = payload.run_id
        dataset_name = payload.dataset_name.lower()
        dag_id = payload.dag_id

        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail=f"Model path not found at {model_path}")

        # Determine target model name in final_model
        final_model_dir = FINAL_MODEL_DIR
        os.makedirs(final_model_dir, exist_ok=True)

        # 1. Resolve ds_number
        if "manufacturing" in dataset_name:
            ds_number = "ds3"
        elif "equipment_anomaly" in dataset_name:
            ds_number = "ds4"
        else:
            ds_number = os.path.splitext(os.path.basename(payload.dataset_name))[0]

        # 2. Resolve family_id from Excel
        family_id = "F0"
        excel_path = ALGO_FAMILIES_XLSX
        if os.path.exists(excel_path):
            try:
                import pandas as pd
                df_families = pd.read_excel(excel_path)
                match = df_families[df_families["DAG ID"] == dag_id]
                if not match.empty:
                    family_id = str(match.iloc[0]["FAMILY_ID"])
            except Exception as e:
                print("Error loading FAMILY_ID from Excel:", e)

        # 3. Format name according to: ds_number_family_id_algo_id
        target_name = f"{ds_number}_{family_id}_{dag_id}.pkl"


        target_path = os.path.join(final_model_dir, target_name)
        
        # Copy file
        shutil.copy(model_path, target_path)

        # Also save a copy inside workspace_data/{ds_number}/ for findability
        workspace_ds_dir = os.path.dirname(model_path)
        workspace_copy_path = os.path.join(workspace_ds_dir, target_name)
        shutil.copy(model_path, workspace_copy_path)

        return {
            "status": "success",
            "model_file": target_name,
            "target_path": target_path,
            "endpoint_url": f"http://127.0.0.1:8001/api/v1/predict/{run_id}"
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Deploy error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    should_reload = os.environ.get("AIC_RELOAD", "0").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8008, reload=should_reload)
