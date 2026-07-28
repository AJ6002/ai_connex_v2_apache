from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import pandas as pd
from sklearn.model_selection import train_test_split

app = FastAPI(
    title="Data Splitting API",
    description="Splits prepared datasets into train, validation, and test subsets.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SplitPayload(BaseModel):
    prepared_file_path: str
    recipe: Dict[str, Any]
    run_id: str
    target_column: Optional[str] = None

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "Split API"}

@app.post("/api/v1/split")
def split_data(payload: SplitPayload):
    try:
        prep_path = payload.prepared_file_path
        recipe = payload.recipe
        run_id = payload.run_id
        target_col = payload.target_column

        if not os.path.exists(prep_path):
            raise HTTPException(status_code=404, detail=f"Prepared dataset file not found at {prep_path}")

        df = pd.read_csv(prep_path)

        test_size = recipe.get("test_size", 0.2)
        val_size = recipe.get("val_size", 0.1)
        stratify_flag = recipe.get("stratify", False)

        # Check if target column exists
        stratify_col = None
        if stratify_flag and target_col and target_col in df.columns:
            # Only stratify if target is discrete and has no NaN and each class has >= 2 samples
            y = df[target_col].dropna()
            if len(y) == len(df) and df[target_col].nunique() > 1:
                class_counts = df[target_col].value_counts()
                if class_counts.min() >= 2:
                    stratify_col = df[target_col]

        # Calculate ratios
        # We split into (Train + Val) and Test first
        # Then split (Train + Val) into Train and Val
        val_test_ratio = test_size + val_size
        if val_test_ratio >= 1.0 or val_test_ratio <= 0.0:
            # Fallback to standard 70/15/15
            test_size = 0.15
            val_size = 0.15
            val_test_ratio = 0.3

        # Correct splitting flow:
        # 1. Split out test set
        if stratify_col is not None:
            try:
                train_val_df, test_df = train_test_split(df, test_size=test_size, stratify=stratify_col, random_state=42)
            except Exception:
                train_val_df, test_df = train_test_split(df, test_size=test_size, random_state=42)
        else:
            train_val_df, test_df = train_test_split(df, test_size=test_size, random_state=42)
        
        # 2. Split train_val into train and val
        val_ratio_scaled = val_size / (1.0 - test_size)
        if val_ratio_scaled >= 1.0 or val_ratio_scaled <= 0.0:
            val_ratio_scaled = 0.15 # fallback
            
        train_df, val_df = train_test_split(train_val_df, test_size=val_ratio_scaled, random_state=42)

        # Save paths
        workspace_data_dir = os.path.dirname(prep_path)
        os.makedirs(workspace_data_dir, exist_ok=True)

        train_path = os.path.join(workspace_data_dir, f"train_{run_id}.csv")
        val_path = os.path.join(workspace_data_dir, f"val_{run_id}.csv")
        test_path = os.path.join(workspace_data_dir, f"test_{run_id}.csv")

        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)

        return {
            "status": "success",
            "train_path": train_path,
            "val_path": val_path,
            "test_path": test_path
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Split error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8004, reload=True)
