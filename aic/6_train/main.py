from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import pickle
import pandas as pd
import numpy as np

# Import scikit-learn models
from sklearn.linear_model import LogisticRegression, LinearRegression, HuberRegressor, Ridge, Lasso
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans

app = FastAPI(
    title="Model Training API",
    description="Fits machine learning models according to compiled training recipes.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TrainPayload(BaseModel):
    train_path: str
    val_path: str
    test_path: Optional[str] = None
    target_column: Optional[str] = None
    recipe: Dict[str, Any]
    run_id: str

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "Train API"}

@app.post("/api/v1/train")
def train_model(payload: TrainPayload):
    try:
        train_path = payload.train_path
        val_path = payload.val_path
        test_path = payload.test_path
        target_col = payload.target_column
        recipe = payload.recipe
        run_id = payload.run_id

        if not os.path.exists(train_path):
            raise HTTPException(status_code=404, detail=f"Train partition not found at {train_path}")

        # Fallback for test_path if not provided
        if not test_path:
            test_path = train_path.replace("train_run_", "test_run_")
            if not os.path.exists(test_path):
                # Fallback to val if test split doesn't exist
                test_path = val_path

        # Add project root directory to path for imports
        import sys
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)

        # 1. Resolve metadata paths
        root_dir = os.path.dirname(os.path.dirname(__file__)) # aic/
        meta1_path = os.path.join(root_dir, "1_dataset_profiler", "meta", "meta1.json")
        meta2_path = os.path.join(root_dir, "2_dag", "meta", "meta2.json")
        meta3_path = os.path.join(root_dir, "3_recipe_orchestrator", "meta", "meta3.json")

        workspace_data_dir = os.path.dirname(train_path)
        os.makedirs(workspace_data_dir, exist_ok=True)
        model_path = os.path.join(workspace_data_dir, f"model_{run_id}.pkl")

        # 2. Call Bridge to build training_manifest.json
        from bridge import aic_meta_to_training_manifest
        manifest_dict, _ = aic_meta_to_training_manifest(
            meta1_path=meta1_path,
            meta2_path=meta2_path,
            meta3_path=meta3_path,
            train_path=train_path,
            val_path=val_path,
            test_path=test_path,
            run_id=run_id,
            output_model_path=model_path
        )

        ml_task = manifest_dict.get("ml_task", "regression")
        feature_cols = manifest_dict["schema_config"]["raw_features"]

        # 3. Invoke aiconnex_ml modeling pipeline
        if ml_task == "anomaly":
            print("[Train API] Running Anomaly Detection Training using aiconnex_ml...")
            df_train = pd.read_csv(train_path)
            df_val = pd.read_csv(val_path)
            df_test = pd.read_csv(test_path)
            
            # Keep labels if present
            fault_col = manifest_dict.get("label_contract", {}).get("fault_label_column")
            y_val_true = df_val[fault_col].values if fault_col and fault_col in df_val.columns else None
            y_test_true = df_test[fault_col].values if fault_col and fault_col in df_test.columns else None

            from aiconnex_ml.anomaly.trainer import AnomalyTrainer
            trainer = AnomalyTrainer(manifest_dict)
            manifest_dict = trainer.run(
                df_train, df_val, df_test, feature_cols,
                y_val_true=y_val_true, y_test_true=y_test_true
            )
            best_algo = manifest_dict.get("results", {}).get("best_algorithm", "Isolation Forest")

        elif ml_task == "regression":
            print("[Train API] Running Regression Training using aiconnex_ml...")
            df_train = pd.read_csv(train_path)
            df_val = pd.read_csv(val_path)
            df_test = pd.read_csv(test_path)

            target_column = manifest_dict["label_contract"]["target_column"]

            # Drop missing rows for arrays
            df_train = df_train.dropna(subset=[target_column]).reset_index(drop=True)
            df_val = df_val.dropna(subset=[target_column]).reset_index(drop=True)
            df_test = df_test.dropna(subset=[target_column]).reset_index(drop=True)

            X_train = df_train[feature_cols].values
            y_train = df_train[target_column].values
            X_val = df_val[feature_cols].values
            y_val = df_val[target_column].values
            X_test = df_test[feature_cols].values
            y_test = df_test[target_column].values

            from aiconnex_ml.regression.trainer import RegressionTrainer
            trainer = RegressionTrainer(manifest_dict)
            manifest_dict = trainer.run(
                X_train, y_train, X_val, y_val, X_test, y_test,
                feature_cols=feature_cols, df_test=df_test
            )
            best_algo = manifest_dict.get("results", {}).get("best_algorithm", "Ridge Regression")
            
        else:
            raise NotImplementedError(f"Training for task type {ml_task} is not supported.")

        return {
            "status": "success",
            "model_path": model_path,
            "algorithm": best_algo,
            "variant": "Standard"
        }

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        try:
            print(tb)
        except UnicodeEncodeError:
            print(tb.encode("ascii", errors="replace").decode("ascii"))
        raise HTTPException(status_code=500, detail=f"Train error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8005, reload=True)
