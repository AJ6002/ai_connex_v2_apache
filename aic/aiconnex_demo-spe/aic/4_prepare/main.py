from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder

app = FastAPI(
    title="Data Preparation API",
    description="Cleans, imputes, encodes, and scales tabular datasets.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PreparePayload(BaseModel):
    raw_file_path: str
    recipe: Dict[str, Any]
    run_id: str
    target_column: Optional[str] = None
    manifest_path: Optional[str] = None

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "Prepare API"}

@app.post("/api/v1/prepare")
def prepare_data(payload: PreparePayload):
    try:
        raw_path = payload.raw_file_path
        recipe = payload.recipe
        run_id = payload.run_id
        target_col = payload.target_column

        # Path resolution against aic root directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.isabs(raw_path):
            candidate_path = os.path.normpath(os.path.join(base_dir, raw_path))
            if os.path.exists(candidate_path):
                raw_path = candidate_path

        if not os.path.exists(raw_path):
            raise HTTPException(status_code=404, detail=f"Raw dataset file not found at {payload.raw_file_path}")


        # Load raw file
        df = pd.read_csv(raw_path)

        # 1. Identify feature types
        numeric_cols = []
        categorical_cols = []
        
        for col in df.columns:
            if col == target_col:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                if df[col].nunique() <= 2:
                    categorical_cols.append(col)
                else:
                    numeric_cols.append(col)
            else:
                categorical_cols.append(col)

        # 2. Imputation
        impute_strategy = recipe.get("impute_strategy", "mean")
        for col in df.columns:
            if df[col].isna().sum() > 0:
                if col in numeric_cols or col == target_col:
                    if impute_strategy == "mean":
                        df[col] = df[col].fillna(df[col].mean())
                    elif impute_strategy == "median":
                        df[col] = df[col].fillna(df[col].median())
                    else:
                        df[col] = df[col].fillna(0)
                else:
                    if df[col].nunique() > 0:
                        mode_val = df[col].mode().iloc[0]
                        df[col] = df[col].fillna(mode_val)
                    else:
                        df[col] = df[col].fillna("missing")

        # 3. Outliers (Clip)
        outlier_method = recipe.get("outlier_method", "none")
        if outlier_method == "iqr" and numeric_cols:
            for col in numeric_cols:
                q25 = df[col].quantile(0.25)
                q75 = df[col].quantile(0.75)
                iqr = q75 - q25
                if iqr > 0:
                    lower = q25 - 1.5 * iqr
                    upper = q75 + 1.5 * iqr
                    df[col] = np.clip(df[col], lower, upper)
        elif outlier_method == "z-score" and numeric_cols:
            for col in numeric_cols:
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    df[col] = np.clip(df[col], mean - 3*std, mean + 3*std)

        # 4. Scaling
        scale_method = recipe.get("scale_method", "none")
        if scale_method != "none" and numeric_cols:
            if scale_method == "standard":
                scaler = StandardScaler()
            elif scale_method == "min-max":
                scaler = MinMaxScaler()
            else:
                scaler = None
                
            if scaler is not None:
                df[numeric_cols] = scaler.fit_transform(df[numeric_cols].astype(float))

        # 5. Encoding
        encode_strategy = recipe.get("encode_strategy", "none")
        if categorical_cols and encode_strategy != "none":
            if encode_strategy == "one-hot":
                df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
            else:
                for col in categorical_cols:
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col].astype(str))

        # Save prepared dataset
        workspace_data_dir = os.path.dirname(raw_path)
        os.makedirs(workspace_data_dir, exist_ok=True)
        prepared_path = os.path.join(workspace_data_dir, f"prepared_{run_id}.csv")
        df.to_csv(prepared_path, index=False)

        # ── Sprint 1: Write quality_report & data_info to shared manifest ────────
        manifest_path = payload.manifest_path
        if manifest_path:
            try:
                manifest = {}
                if os.path.exists(manifest_path):
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                else:
                    dir_n = os.path.dirname(manifest_path)
                    if dir_n:
                        os.makedirs(dir_n, exist_ok=True)

                # Compute quality report
                null_cols = {col: round(df[col].isna().mean(), 4)
                             for col in df.columns if df[col].isna().mean() > 0.01}
                stuck_sensors = [col for col in numeric_cols if df[col].std() == 0]

                manifest["data_info"] = {
                    "num_rows": int(len(df)),
                    "num_features": int(len(df.columns)),
                    "prepared_file_path": prepared_path,
                    "quality_report": {
                        "high_null_columns": null_cols,
                        "stuck_sensors": stuck_sensors,
                        "outlier_method_applied": outlier_method,
                        "scale_method_applied": scale_method,
                    }
                }
                manifest["pipeline_step"] = "prepare"

                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[Prepare] Warning: Could not update manifest: {e}")


        return {
            "status": "success",
            "prepared_file_path": prepared_path
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Prepare error: {str(e)}")


class ComparePayload(BaseModel):
    raw_file_path: str
    prepared_file_path: str
    target_column: Optional[str] = None

@app.post("/api/v1/prepare/compare")
def compare_prepare(payload: ComparePayload):
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        raw_path = payload.raw_file_path
        if not os.path.isabs(raw_path):
            cand = os.path.normpath(os.path.join(base_dir, raw_path))
            if os.path.exists(cand):
                raw_path = cand
                
        prep_path = payload.prepared_file_path
        if not os.path.isabs(prep_path):
            cand = os.path.normpath(os.path.join(base_dir, prep_path))
            if os.path.exists(cand):
                prep_path = cand

        raw_df = pd.read_csv(raw_path) if os.path.exists(raw_path) else None
        prep_df = pd.read_csv(prep_path) if os.path.exists(prep_path) else None

        raw_rows = len(raw_df) if raw_df is not None else 0
        raw_cols = len(raw_df.columns) if raw_df is not None else 0
        raw_nulls = int(raw_df.isna().sum().sum()) if raw_df is not None else 0

        prep_rows = len(prep_df) if prep_df is not None else 0
        prep_cols = len(prep_df.columns) if prep_df is not None else 0
        prep_nulls = int(prep_df.isna().sum().sum()) if prep_df is not None else 0

        cols_audit = []
        if raw_df is not None and prep_df is not None:
            for col in prep_df.columns:
                if col in raw_df.columns:
                    raw_col_nulls = int(raw_df[col].isna().sum())
                    prep_col_nulls = int(prep_df[col].isna().sum())
                    is_num = pd.api.types.is_numeric_dtype(prep_df[col])
                    raw_min = float(raw_df[col].min()) if is_num and not raw_df[col].dropna().empty else 0.0
                    raw_max = float(raw_df[col].max()) if is_num and not raw_df[col].dropna().empty else 0.0
                    prep_min = float(prep_df[col].min()) if is_num and not prep_df[col].dropna().empty else 0.0
                    prep_max = float(prep_df[col].max()) if is_num and not prep_df[col].dropna().empty else 0.0
                    
                    changed = raw_col_nulls > 0 or raw_min != prep_min or raw_max != prep_max
                    cols_audit.append({
                        "column": col,
                        "type": "numeric" if is_num else "categorical",
                        "raw_nulls": raw_col_nulls,
                        "prep_nulls": prep_col_nulls,
                        "raw_min": raw_min,
                        "raw_max": raw_max,
                        "prep_min": prep_min,
                        "prep_max": prep_max,
                        "changed": changed
                    })

        return {
            "status": "success",
            "summary": {
                "total_rows": prep_rows,
                "total_columns": prep_cols,
                "total_nulls_before": raw_nulls,
                "total_nulls_after": prep_nulls
            },
            "columns": cols_audit,
            "raw_summary": {
                "num_rows": raw_rows,
                "num_cols": raw_cols,
                "total_nulls": raw_nulls,
                "null_percentage": round((raw_nulls / (raw_rows * raw_cols * 1.0)) * 100, 2) if (raw_rows * raw_cols) > 0 else 0.0
            },
            "prepared_summary": {
                "num_rows": prep_rows,
                "num_cols": prep_cols,
                "total_nulls": prep_nulls,
                "null_percentage": round((prep_nulls / (prep_rows * prep_cols * 1.0)) * 100, 2) if (prep_rows * prep_cols) > 0 else 0.0
            },
            "comparison_metrics": {
                "nulls_removed": raw_nulls - prep_nulls,
                "imputation_applied": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compare error: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    should_reload = os.environ.get("AIC_RELOAD", "0").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=should_reload)

