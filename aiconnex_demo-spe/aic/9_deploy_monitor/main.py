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
        base_dir = AIC_ROOT
        def resolve_file_path(p: Optional[str]) -> Optional[str]:
            if not p:
                return p
            abs_p = p if os.path.isabs(p) else os.path.normpath(os.path.join(base_dir, p))
            if os.path.exists(abs_p):
                return abs_p
            # Try stripping '/splits/' or '\splits\'
            alt_p = abs_p.replace("\\splits\\", "\\").replace("/splits/", "/")
            if os.path.exists(alt_p):
                return alt_p
            # Try inserting '/splits/' before filename
            dir_name, file_name = os.path.split(abs_p)
            alt_p2 = os.path.join(dir_name, "splits", file_name)
            if os.path.exists(alt_p2):
                return alt_p2
            return abs_p

        model_path = resolve_file_path(payload.model_path)
        run_id = payload.run_id
        dataset_name = payload.dataset_name.lower()
        dag_id = payload.dag_id

        if not model_path or not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail=f"Model path not found at {payload.model_path}")



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
            "endpoint_url": f"http://127.0.0.1:8008/api/v1/predict/{run_id}"
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Deploy error: {str(e)}")


class PredictPayload(BaseModel):
    run_id: Optional[str] = None
    features: Optional[Any] = None
    data: Optional[Any] = None


@app.post("/api/v1/predict/{run_id}")
@app.post("/api/v1/predict")
def predict_endpoint(payload: Optional[PredictPayload] = None, run_id: Optional[str] = None):
    try:
        import pickle
        import time
        import pandas as pd
        import numpy as np

        start_t = time.time()
        req_payload = payload or PredictPayload()
        effective_run_id = run_id or req_payload.run_id or "default"

        # 1. Locate model .pkl file
        base_dir = AIC_ROOT
        model_path = None

        # Check final_model directory first
        final_dir = FINAL_MODEL_DIR
        if os.path.exists(final_dir):
            for fname in os.listdir(final_dir):
                if fname.endswith(".pkl"):
                    model_path = os.path.join(final_dir, fname)
                    break

        # Fallback to workspace_data matching run_id
        ws_dir = os.path.join(base_dir, "workspace_data")
        if not model_path and os.path.exists(ws_dir):
            for root, dirs, files in os.walk(ws_dir):
                for f in files:
                    if effective_run_id in f and f.endswith(".pkl") and f.startswith("model_"):
                        model_path = os.path.join(root, f)
                        break
                if model_path:
                    break

        # Fallback to any model .pkl in workspace_data
        if not model_path and os.path.exists(ws_dir):
            for root, dirs, files in os.walk(ws_dir):
                for f in files:
                    if f.endswith(".pkl") and f.startswith("model_"):
                        model_path = os.path.join(root, f)
                        break
                if model_path:
                    break

        if not model_path or not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail=f"No deployed model binary found for run_id '{effective_run_id}'")

        # 2. Load model & scaler
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        scaler = None
        scaler_path = model_path.replace("model_", "scaler_")
        if os.path.exists(scaler_path):
            with open(scaler_path, "rb") as f:
                scaler = pickle.load(f)

        # 3. Parse input features
        raw_input = req_payload.features if req_payload.features is not None else req_payload.data
        if raw_input is None:
            # Default dummy sample if features not passed
            raw_input = [[0.0] * (getattr(model, "n_features_in_", 10))]

        if isinstance(raw_input, dict):
            df_in = pd.DataFrame([raw_input])
        elif isinstance(raw_input, list):
            if raw_input and isinstance(raw_input[0], dict):
                df_in = pd.DataFrame(raw_input)
            elif raw_input and isinstance(raw_input[0], list):
                df_in = pd.DataFrame(raw_input)
            else:
                df_in = pd.DataFrame([raw_input])
        elif isinstance(raw_input, (int, float)):
            df_in = pd.DataFrame([[raw_input]])
        else:
            df_in = pd.DataFrame(raw_input)

        # Coerce numeric dtypes & fillna
        for col in df_in.columns:
            if not pd.api.types.is_numeric_dtype(df_in[col]):
                df_in[col] = pd.to_numeric(df_in[col], errors="coerce")
        df_in = df_in.fillna(0)

        # Feature alignment
        expected_n = getattr(model, "n_features_in_", df_in.shape[1])
        if scaler is not None and hasattr(scaler, "feature_names_in_"):
            df_in = df_in.reindex(columns=scaler.feature_names_in_, fill_value=0)
        elif hasattr(model, "feature_names_in_"):
            df_in = df_in.reindex(columns=model.feature_names_in_, fill_value=0)
        elif df_in.shape[1] != expected_n:
            if df_in.shape[1] > expected_n:
                df_in = df_in.iloc[:, :expected_n]
            else:
                pad_cols = [f"pad_{i}" for i in range(expected_n - df_in.shape[1])]
                pad_df = pd.DataFrame(0, index=df_in.index, columns=pad_cols)
                df_in = pd.concat([df_in, pad_df], axis=1)

        X_in = scaler.transform(df_in) if (scaler is not None and hasattr(scaler, "transform")) else df_in.values

        preds = model.predict(X_in)

        # Convert numpy arrays to Python list
        preds_list = preds.tolist() if hasattr(preds, "tolist") else list(preds)
        latency_ms = round((time.time() - start_t) * 1000, 2)

        return {
            "status": "success",
            "run_id": effective_run_id,
            "model_path": model_path,
            "predictions": preds_list,
            "sample_count": len(preds_list),
            "latency_ms": latency_ms
        }
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Inference error: {str(exc)}")


if __name__ == "__main__":
    import uvicorn
    should_reload = os.environ.get("AIC_RELOAD", "0").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8008, reload=should_reload)

