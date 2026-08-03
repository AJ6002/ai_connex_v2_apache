from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, RobustScaler


# ── Robust Path Resolver ──────────────────────────────────────────────────────
def resolve_path(p: str) -> str:
    if not p:
        return p
    p = p.replace("\\", "/").strip()
    if os.path.isabs(p):
        return p
    # Try relative to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    abs_p = os.path.abspath(os.path.join(script_dir, p))
    if os.path.exists(abs_p):
        return abs_p
    # Try relative to the workspace root (aic/)
    workspace_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    root_p = os.path.join(workspace_root, p)
    if os.path.exists(root_p):
        return root_p
    # Handle 'services/' prefix
    if p.startswith("services/"):
        strip_p = p.replace("services/", "", 1)
        services_dir = os.path.abspath(os.path.join(script_dir, ".."))
        svc_p = os.path.join(services_dir, strip_p)
        if os.path.exists(svc_p):
            return svc_p
    # Fallback to default join with workspace root
    return os.path.join(workspace_root, p)

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
        raw_path = resolve_path(payload.raw_file_path)
        recipe = payload.recipe
        run_id = payload.run_id
        target_col = payload.target_column

        if not os.path.exists(raw_path):
            raise HTTPException(status_code=404, detail=f"Raw dataset file not found at {raw_path}")

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
                    elif impute_strategy in ("mode", "most_frequent"):
                        if df[col].nunique() > 0:
                            df[col] = df[col].fillna(df[col].mode().iloc[0])
                        else:
                            df[col] = df[col].fillna(0)
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
        scale_method = str(recipe.get("scale_method", "none")).lower()
        if scale_method != "none" and numeric_cols:
            if scale_method in ("standard", "standardize"):
                scaler = StandardScaler()
            elif scale_method in ("minmax", "min-max"):
                scaler = MinMaxScaler()
            elif scale_method == "robust":
                scaler = RobustScaler()
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
        if run_id:
            services_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            workspace_data_dir = os.path.join(services_dir, "workspace_data", run_id)
        else:
            workspace_data_dir = os.path.dirname(raw_path)
        os.makedirs(workspace_data_dir, exist_ok=True)
        
        orig_filename = os.path.basename(raw_path)
        dataset_stem = os.path.splitext(orig_filename)[0]
        if dataset_stem.startswith("dag_"):
            dataset_stem = dataset_stem[4:]
        elif dataset_stem.startswith("profiled_"):
            dataset_stem = dataset_stem[9:]
        elif dataset_stem.startswith("compiled_"):
            dataset_stem = dataset_stem[9:]
            
        prepared_path = os.path.join(workspace_data_dir, f"prepare_{dataset_stem}.csv")
        df.to_csv(prepared_path, index=False)

        # ── Sprint 1: Write quality_report & data_info to shared manifest ────────
        manifest_path = payload.manifest_path
        if manifest_path and os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)

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
def compare_datasets(payload: ComparePayload):
    try:
        raw_path = resolve_path(payload.raw_file_path)
        prep_path = resolve_path(payload.prepared_file_path)
        target_col = payload.target_column

        if not os.path.exists(raw_path) or not os.path.exists(prep_path):
            raise HTTPException(status_code=404, detail=f"Raw or prepared file not found on disk. raw: {raw_path}, prep: {prep_path}")

        df_raw = pd.read_csv(raw_path)
        df_prep = pd.read_csv(prep_path)

        cols_comparison = []
        cleaning_actions = []

        common_cols = [c for c in df_raw.columns if c in df_prep.columns]

        for col in common_cols:
            if col == target_col:
                continue
            
            raw_nulls = int(df_raw[col].isna().sum())
            prep_nulls = int(df_prep[col].isna().sum())

            if pd.api.types.is_numeric_dtype(df_raw[col]) and pd.api.types.is_numeric_dtype(df_prep[col]):
                raw_min = float(df_raw[col].min()) if not df_raw[col].empty else 0.0
                raw_max = float(df_raw[col].max()) if not df_raw[col].empty else 0.0
                prep_min = float(df_prep[col].min()) if not df_prep[col].empty else 0.0
                prep_max = float(df_prep[col].max()) if not df_prep[col].empty else 0.0
                
                col_changed = not df_raw[col].equals(df_prep[col])
                
                cols_comparison.append({
                    "column": col,
                    "type": "numeric",
                    "raw_nulls": raw_nulls,
                    "prep_nulls": prep_nulls,
                    "raw_min": raw_min,
                    "raw_max": raw_max,
                    "prep_min": prep_min,
                    "prep_max": prep_max,
                    "changed": col_changed
                })

                if raw_nulls > 0:
                    cleaning_actions.append({
                        "column": col,
                        "action": f"Imputed {raw_nulls} missing values",
                        "strategy": "Median Imputation",
                        "why": "Standard estimators cannot calculate metrics with missing values. Imputing with median values preserves statistical centrality without introducing variance drift.",
                        "how": "Replaced NaN markers with column median value."
                    })
                
                if raw_max > prep_max or raw_min < prep_min:
                    cleaning_actions.append({
                        "column": col,
                        "action": "Clipped outlier values",
                        "strategy": "IQR Outlier Clipping",
                        "why": "Extreme outlier spikes skew variance-based scaling algorithms and cause linear regression weights to drift. Clipping outliers stabilizes training.",
                        "how": f"Bounded values within the interval [{prep_min:.2f}, {prep_max:.2f}] based on Interquartile Range thresholds."
                    })
            else:
                col_changed = not df_raw[col].equals(df_prep[col])
                cols_comparison.append({
                    "column": col,
                    "type": "categorical",
                    "raw_nulls": raw_nulls,
                    "prep_nulls": prep_nulls,
                    "changed": col_changed
                })
                
                if raw_nulls > 0:
                    cleaning_actions.append({
                        "column": col,
                        "action": f"Imputed {raw_nulls} missing categorical codes",
                        "strategy": "Mode Imputation",
                        "why": "Missing string tags break category encoding dictionaries. Imputing using the category mode stabilizes factor mapping.",
                        "how": "Replaced NaNs with the column category mode."
                    })

        # Calculate target column variance
        target_var_before = 0.0
        target_var_after = 0.0
        target_nunique = 0
        if target_col:
            if target_col in df_raw.columns:
                target_nunique = int(df_raw[target_col].nunique())
                if pd.api.types.is_numeric_dtype(df_raw[target_col]):
                    target_var_before = float(df_raw[target_col].var()) if len(df_raw) > 1 else 0.0
            if target_col in df_prep.columns:
                if pd.api.types.is_numeric_dtype(df_prep[target_col]):
                    target_var_after = float(df_prep[target_col].var()) if len(df_prep) > 1 else 0.0

        return {
            "status": "success",
            "columns": cols_comparison,
            "actions": cleaning_actions,
            "summary": {
                "total_rows": len(df_raw),
                "total_columns": len(df_raw.columns),
                "total_nulls_before": int(df_raw.isna().sum().sum()),
                "total_nulls_after": int(df_prep.isna().sum().sum()),
                "target_column": target_col,
                "target_var_before": target_var_before,
                "target_var_after": target_var_after,
                "target_nunique": target_nunique
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    should_reload = os.environ.get("AIC_RELOAD", "0").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=should_reload)
