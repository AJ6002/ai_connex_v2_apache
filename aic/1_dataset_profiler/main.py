import io
import os
import json
import hashlib
import pandas as pd
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from profiler import generate_profile
from detector import detect_family

app = FastAPI(
    title="Dataset Profiler API",
    description="Processes tabular datasets and returns profiling statistics along with recommended ML algorithm families.",
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

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "Dataset Profiler API"}

@app.post("/api/v1/profile")
async def profile_dataset(
    file: UploadFile = File(...),
    target_column: Optional[str] = Form(None)
):
    # Validate file extension
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.json') or filename.endswith('.txt')):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a CSV (.csv), JSON (.json), or TXT (.txt) file."
        )

    try:
        # Read file contents into memory
        contents = await file.read()

        # Derive a safe short directory name to avoid Windows MAX_PATH (260 chars) crashes
        filename_lower = file.filename.lower()
        if "manufacturing" in filename_lower:
            ds_number = "ds3"
        elif "equipment_anomaly" in filename_lower:
            ds_number = "ds4"
        else:
            raw_stem = os.path.splitext(file.filename)[0]
            if len(raw_stem) > 40:
                # Hash the long stem to a safe 12-char identifier
                ds_number = "ds_" + hashlib.md5(raw_stem.encode()).hexdigest()[:12]
            else:
                ds_number = raw_stem

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        workspace_data_dir = os.path.join(base_dir, "workspace_data", ds_number)
        os.makedirs(workspace_data_dir, exist_ok=True)
        saved_file_path = os.path.join(workspace_data_dir, file.filename[:80])  # truncate filename too
        try:
            with open(saved_file_path, "wb") as fout:
                fout.write(contents)
        except OSError:
            # Disk persistence failed (e.g., path too long on Windows) — continue with in-memory path
            saved_file_path = os.path.join(workspace_data_dir, ds_number + ".csv")
            try:
                with open(saved_file_path, "wb") as fout:
                    fout.write(contents)
            except OSError:
                saved_file_path = "<in-memory-only>"
            
        # Read dataset into pandas DataFrame
        if filename.endswith('.csv'):
            decoded = contents.decode('utf-8', errors='ignore')
            df = pd.read_csv(io.StringIO(decoded))
        elif filename.endswith('.txt'):
            decoded = contents.decode('utf-8', errors='ignore')
            df = pd.read_csv(io.StringIO(decoded), sep=r'\s+')
        elif filename.endswith(('.xlsx', '.xls')):
            df_raw = pd.read_excel(io.BytesIO(contents))
            skip_idx = None
            for idx in range(min(15, len(df_raw))):
                row_vals = [str(x).lower() for x in df_raw.iloc[idx].values]
                if any("date" in v or "time" in v or "timestamp" in v for v in row_vals):
                    skip_idx = idx
                    break
            if skip_idx is not None:
                df = pd.read_excel(io.BytesIO(contents), header=skip_idx + 1)
            else:
                df = df_raw
        else:
            decoded = contents.decode('utf-8', errors='ignore')
            df = pd.read_json(io.StringIO(decoded))
            
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse the file: {str(e)}"
        )

    if len(df) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded dataset is empty."
        )

    try:
        # 1. Generate column and dataset statistics
        profile = generate_profile(df)
        
        # 2. Detect the algorithm family
        family_result = detect_family(df, profile, target_hint=target_column)
        
        # 3. Resolve exact DAG ID from the 1690 mapping
        from detector import decide_dag_and_details
        dag_details = decide_dag_and_details(df, profile, family_result)
        
        # 4. Combine result
        profile['algorithm_family'] = family_result['algorithm_family']
        profile['family_confidence'] = family_result['family_confidence']
        profile['family_reason'] = family_result['reason']
        profile['detected_target'] = family_result['target_column']
        profile['suggested_task'] = family_result['suggested_task']
        
        # Add dynamic DAG recommendation fields
        profile['recommended_dag_id'] = dag_details['recommended_dag_id']
        profile['recommended_algorithm'] = dag_details['recommended_algorithm']
        profile['recommended_variant'] = dag_details['recommended_variant']
        profile['recommended_special_handling'] = dag_details['recommended_special_handling']
        profile['raw_file_path'] = saved_file_path

        # ── Correction: Mirror top-level dimension keys so clients don't need to dig into dataset_info
        profile['num_rows'] = profile['dataset_info']['num_rows']
        profile['num_cols'] = profile['dataset_info']['num_columns']
        
        meta_payload = {
            "status": "success",
            "filename": file.filename,
            "profile": profile
        }
        
        # Save meta1.json inside 1_dataset_profiler/meta/
        meta_dir = os.path.join(os.path.dirname(__file__), "meta")
        os.makedirs(meta_dir, exist_ok=True)
        meta_path = os.path.join(meta_dir, "meta1.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_payload, f, indent=2)
            
        return meta_payload
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error during profiling: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the dataset: {str(e)}"
        )

@app.get("/api/v1/masterdata/dag_mapping")
def get_dag_mapping():
    path = os.path.join(os.path.dirname(__file__), "dag_mapping.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="dag_mapping.json not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/v1/masterdata/dag_conditions_mapping")
def get_dag_conditions_mapping():
    path = os.path.join(os.path.dirname(__file__), "dag_conditions_mapping.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="dag_conditions_mapping.json not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/v1/masterdata/algorithm_families")
def get_algorithm_families():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "algorithm_families_complete.xlsx")
    if not os.path.exists(path):
        path = os.path.join(base_dir, "algorithm_families.xlsx")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Algorithm families excel not found")
    df = pd.read_excel(path)
    # Replace NaN with None so it translates cleanly to JSON null
    df = df.replace({np.nan: None})
    return {"headers": df.columns.tolist(), "records": df.to_dict(orient="records")}

@app.get("/api/v1/masterdata/boilerplate_metadata")
def get_boilerplate_metadata():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "boilerplate_metadata.xlsx")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="boilerplate_metadata.xlsx not found")
    df = pd.read_excel(path)
    # Replace NaN with None
    df = df.replace({np.nan: None})
    return {"headers": df.columns.tolist(), "records": df.to_dict(orient="records")}

@app.get("/api/v1/masterdata/boilerplate_profiler_readme")
def get_boilerplate_profiler_readme():
    path = os.path.join(os.path.dirname(__file__), "README.md")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="README.md not found")
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@app.get("/api/v1/masterdata/boilerplate_dag_readme")
def get_boilerplate_dag_readme():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "2_dag", "README.md")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="README.md not found")
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@app.get("/api/v1/masterdata/boilerplate_recipe_readme")
def get_boilerplate_recipe_readme():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "3_recipe_orchestrator", "README.md")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="README.md not found")
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@app.get("/api/v1/masterdata/recipe/{dag_id}")
def get_recipe(dag_id: str):
    import json
    base_dir = os.path.dirname(os.path.dirname(__file__))
    recipe_dir = os.path.join(base_dir, "3_recipe_orchestrator", "recipe")
    
    prep_path = os.path.join(recipe_dir, "preparing", f"{dag_id}.json")
    feat_path = os.path.join(recipe_dir, "feature_engineering", f"{dag_id}.json")
    split_path = os.path.join(recipe_dir, "splitting", f"{dag_id}.json")
    train_path = os.path.join(recipe_dir, "training", f"{dag_id}.json")
    
    fallback_id = "DAG_001"
    try:
        dag_num = int(dag_id.split("_")[1])
    except Exception:
        dag_num = 1
        
    if dag_num >= 1 and dag_num <= 240: fallback_id = "DAG_001"
    elif dag_num >= 241 and dag_num <= 485: fallback_id = "DAG_241"
    elif dag_num >= 486 and dag_num <= 695: fallback_id = "DAG_486"
    elif dag_num >= 696 and dag_num <= 905: fallback_id = "DAG_696"
    elif dag_num >= 906 and dag_num <= 1130: fallback_id = "DAG_906"
    elif dag_num >= 1131 and dag_num <= 1240: fallback_id = "DAG_1131"
    elif dag_num >= 1241 and dag_num <= 1340: fallback_id = "DAG_1241"
    elif dag_num >= 1341 and dag_num <= 1450: fallback_id = "DAG_1341"
    elif dag_num >= 1451 and dag_num <= 1560: fallback_id = "DAG_1451"
    elif dag_num >= 1561 and dag_num <= 1690: fallback_id = "DAG_1561"

    if not os.path.exists(prep_path): prep_path = os.path.join(recipe_dir, "preparing", f"{fallback_id}.json")
    if not os.path.exists(feat_path): feat_path = os.path.join(recipe_dir, "feature_engineering", f"{fallback_id}.json")
    if not os.path.exists(split_path): split_path = os.path.join(recipe_dir, "splitting", f"{fallback_id}.json")
    if not os.path.exists(train_path): train_path = os.path.join(recipe_dir, "training", f"{fallback_id}.json")
        
    try:
        with open(prep_path, "r", encoding="utf-8") as f: prep_data = json.load(f)
        with open(feat_path, "r", encoding="utf-8") as f: feat_data = json.load(f)
        with open(split_path, "r", encoding="utf-8") as f: split_data = json.load(f)
        with open(train_path, "r", encoding="utf-8") as f: train_data = json.load(f)
        return {
            "preparing": prep_data,
            "feature_engineering": feat_data,
            "splitting": split_data,
            "training": train_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read recipe files: {str(e)}")

@app.post("/api/v1/masterdata/recipe/{dag_id}")
def save_recipe(dag_id: str, payload: dict):
    import json
    base_dir = os.path.dirname(os.path.dirname(__file__))
    recipe_dir = os.path.join(base_dir, "3_recipe_orchestrator", "recipe")
    
    prep_path = os.path.join(recipe_dir, "preparing", f"{dag_id}.json")
    feat_path = os.path.join(recipe_dir, "feature_engineering", f"{dag_id}.json")
    split_path = os.path.join(recipe_dir, "splitting", f"{dag_id}.json")
    train_path = os.path.join(recipe_dir, "training", f"{dag_id}.json")
    
    try:
        if "preparing" in payload:
            os.makedirs(os.path.dirname(prep_path), exist_ok=True)
            with open(prep_path, "w", encoding="utf-8") as f: json.dump(payload["preparing"], f, indent=4)
        if "feature_engineering" in payload:
            os.makedirs(os.path.dirname(feat_path), exist_ok=True)
            with open(feat_path, "w", encoding="utf-8") as f: json.dump(payload["feature_engineering"], f, indent=4)
        if "splitting" in payload:
            os.makedirs(os.path.dirname(split_path), exist_ok=True)
            with open(split_path, "w", encoding="utf-8") as f: json.dump(payload["splitting"], f, indent=4)
        if "training" in payload:
            os.makedirs(os.path.dirname(train_path), exist_ok=True)
            with open(train_path, "w", encoding="utf-8") as f: json.dump(payload["training"], f, indent=4)
        return {"status": "success", "message": f"Recipes for {dag_id} saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {str(e)}")

class ProfilePlotPayload(BaseModel):
    file_path: str
    column: Optional[str] = None

@app.post("/api/v1/plots/correlation")
def get_correlation_plot(payload: ProfilePlotPayload):
    try:
        if not os.path.exists(payload.file_path):
            raise HTTPException(status_code=404, detail="Dataset file not found")
        df = pd.read_csv(payload.file_path)
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {"columns": [], "matrix": []}
        cols = list(numeric_df.columns[:12])
        corr_matrix = numeric_df[cols].corr().fillna(0).round(3).values.tolist()
        return {"columns": cols, "matrix": corr_matrix}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/plots/distribution")
def get_distribution_plot(payload: ProfilePlotPayload):
    try:
        if not os.path.exists(payload.file_path):
            raise HTTPException(status_code=404, detail="Dataset file not found")
        df = pd.read_csv(payload.file_path)
        col = payload.column or (df.columns[0] if len(df.columns) > 0 else None)
        if not col or col not in df.columns:
            return {"column": col, "bins": [], "counts": []}
        series = df[col].dropna()
        if pd.api.types.is_numeric_dtype(series):
            counts, bin_edges = np.histogram(series, bins=15)
            bins = [f"{round(bin_edges[i],2)}-{round(bin_edges[i+1],2)}" for i in range(len(counts))]
            return {"column": col, "type": "numeric", "bins": bins, "counts": counts.tolist()}
        else:
            val_counts = series.value_counts().head(10)
            return {"column": col, "type": "categorical", "bins": val_counts.index.tolist(), "counts": val_counts.values.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/plots/missing_matrix")
def get_missing_matrix_plot(payload: ProfilePlotPayload):
    try:
        if not os.path.exists(payload.file_path):
            raise HTTPException(status_code=404, detail="Dataset file not found")
        df = pd.read_csv(payload.file_path)
        missing_counts = df.isna().sum()
        missing_pcts = (missing_counts / len(df) * 100).round(2)
        return {
            "columns": list(df.columns),
            "missing_counts": missing_counts.tolist(),
            "missing_percentages": missing_pcts.tolist(),
            "total_rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/plots/outliers")
def get_outliers_plot(payload: ProfilePlotPayload):
    try:
        if not os.path.exists(payload.file_path):
            raise HTTPException(status_code=404, detail="Dataset file not found")
        df = pd.read_csv(payload.file_path)
        col = payload.column or ([c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])][:1] or [df.columns[0]])[0]
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            return {"column": col, "outliers_count": 0}
        series = df[col].dropna()
        q25, q75 = series.quantile(0.25), series.quantile(0.75)
        iqr = q75 - q25
        lower, upper = q25 - 1.5 * iqr, q75 + 1.5 * iqr
        outliers = series[(series < lower) | (series > upper)]
        return {
            "column": col,
            "min": round(float(series.min()), 2),
            "q25": round(float(q25), 2),
            "median": round(float(series.median()), 2),
            "q75": round(float(q75), 2),
            "max": round(float(series.max()), 2),
            "iqr_lower": round(float(lower), 2),
            "iqr_upper": round(float(upper), 2),
            "outliers_count": len(outliers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/masterdata/dag_mapping")
def save_dag_mapping(payload: dict):
    import json
    path1 = os.path.join(os.path.dirname(__file__), "dag_mapping.json")
    path2 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "2_dag", "dag_mapping.json")
    try:
        with open(path1, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        with open(path2, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return {"status": "success", "message": "dag_mapping.json updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/masterdata/dag_conditions_mapping")
def save_dag_conditions_mapping(payload: dict):
    import json
    path1 = os.path.join(os.path.dirname(__file__), "dag_conditions_mapping.json")
    path2 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "2_dag", "dag_conditions_mapping.json")
    try:
        with open(path1, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        with open(path2, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return {"status": "success", "message": "dag_conditions_mapping.json updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/masterdata/algorithm_families")
def save_algorithm_families(payload: dict):
    import json
    records = payload.get("records")
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    try:
        df = pd.DataFrame(records)
        base_dir = os.path.dirname(os.path.dirname(__file__))
        path_complete = os.path.join(base_dir, "algorithm_families_complete.xlsx")
        path_families = os.path.join(base_dir, "algorithm_families.xlsx")
        
        # Save to both Excel spreadsheets
        df.to_excel(path_complete, index=False)
        df.to_excel(path_families, index=False)
        
        # Synchronize back to dag_mapping.json
        mapping = {}
        for r in records:
            fam_name = str(r.get("FAMILY_NAME", "")).upper()
            if not fam_name:
                continue
            if fam_name not in mapping:
                mapping[fam_name] = []
            mapping[fam_name].append({
                "dag_id": r.get("DAG ID"),
                "algorithm": r.get("Algorithm"),
                "variant": r.get("Variant"),
                "special_handling": r.get("Special Handling") or ""
            })
            
        path1 = os.path.join(os.path.dirname(__file__), "dag_mapping.json")
        path2 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "2_dag", "dag_mapping.json")
        with open(path1, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2)
        with open(path2, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2)
            
        return {"status": "success", "message": "Algorithm families and dag_mapping.json updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/masterdata/boilerplate_metadata")
def save_boilerplate_metadata(payload: dict):
    records = payload.get("records")
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    try:
        df = pd.DataFrame(records)
        base_dir = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(base_dir, "boilerplate_metadata.xlsx")
        df.to_excel(path, index=False)
        return {"status": "success", "message": "boilerplate_metadata.xlsx updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    should_reload = os.environ.get("AIC_RELOAD", "0").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=should_reload)
