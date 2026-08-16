"""
SageMaker Processing Job: Node 1 - Data Cleaning
===============================================
Cleans the raw dataset, normalizes columns, performs basic imputation,
and outputs clean_dataset.parquet and an initial manifest.json.
"""

import os
import sys
import json
import argparse
import logging
import warnings
import pandas as pd
import boto3
from urllib.parse import urlparse

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Node 1 - Data Cleaning")
    parser.add_argument("--input-path", type=str, required=True, help="Path to input raw parquet file")
    parser.add_argument("--output-dir", type=str, required=True, help="S3 or local dir to save clean_dataset.parquet")
    parser.add_argument("--config-path", type=str, required=True, help="Path to input config.json")
    return parser.parse_known_args()[0]

def load_json(path: str):
    if path.startswith("s3://"):
        parsed = urlparse(path)
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip('/'))
        return json.loads(obj['Body'].read().decode('utf-8'))
    else:
        with open(path, 'r') as f:
            return json.load(f)

def save_file(local_path: str, target_dir: str):
    filename = os.path.basename(local_path)
    if target_dir.startswith("s3://"):
        parsed = urlparse(target_dir)
        bucket = parsed.netloc
        key = os.path.join(parsed.path.lstrip('/'), filename).replace("\\", "/")
        s3 = boto3.client('s3')
        log.info(f"Uploading {local_path} to s3://{bucket}/{key}")
        s3.upload_file(local_path, bucket, key)
    else:
        os.makedirs(target_dir, exist_ok=True)
        dest = os.path.join(target_dir, filename)
        import shutil
        shutil.copyfile(local_path, dest)
        log.info(f"Saved locally to {dest}")

def main():
    args = parse_args()
    log.info(f"Loading config from: {args.config_path}")
    config = load_json(args.config_path)

    log.info(f"Loading raw dataset from: {args.input_path}")
    if args.input_path.endswith(".parquet") or "parquet" in args.input_path.lower():
        df = pd.read_parquet(args.input_path)
    else:
        df = pd.read_csv(args.input_path)
    log.info(f"Loaded dataset: {df.shape[0]:,} rows x {df.shape[1]} columns")

    schema_config = config.get("schema", {})
    time_idx = schema_config.get("time_index", "cycle")
    identifier = schema_config.get("identifier", "global_engine_id")
    target_col = schema_config.get("target_column", "RUL")

    # Dynamic schema check
    required_cols = [time_idx, identifier]
    if target_col:
        required_cols.append(target_col)
    
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing essential columns in raw data: {missing_cols}")

    # General imputation for numerical columns
    num_cols = df.select_dtypes(include=['number']).columns
    null_counts = df[num_cols].isnull().sum()
    null_total = int(null_counts.sum())
    
    if null_total > 0:
        log.info(f"Imputing {null_total} missing values in numerical columns using forward-fill/mean...")
        for col in num_cols:
            if df[col].isnull().any():
                df[col] = df[col].ffill().bfill().fillna(df[col].mean())

    # De-duplication
    dup_rows = int(df.duplicated().sum())
    if dup_rows > 0:
        log.info(f"Removing {dup_rows} duplicate rows...")
        df = df.drop_duplicates().reset_index(drop=True)

    # Save cleaned Parquet
    os.makedirs("/tmp/clean", exist_ok=True)
    local_parquet = "/tmp/clean/clean_dataset.parquet"
    df.to_parquet(local_parquet, index=False)
    save_file(local_parquet, args.output_dir)

    # Create the initial manifest file
    manifest = {
        "manifest_id": f"manifest-{config.get('pipeline_run_id', 'default')}",
        "project": config.get("project", "aiconnex_ml"),
        "created_at": pd.Timestamp.now().isoformat(),
        "dataset": {
            "uri": os.path.join(args.output_dir, "clean_dataset.parquet").replace("\\", "/"),
            "row_count": int(df.shape[0]),
            "column_count": int(df.shape[1])
        },
        "schema": schema_config,
        "routing_decision": {
            "problem_type": config.get("domain", "regression"),
            "algorithm": config.get("algorithm", "random_forest")
        }
    }

    local_manifest = "/tmp/clean/manifest.json"
    with open(local_manifest, "w") as f:
        json.dump(manifest, f, indent=2)
    save_file(local_manifest, args.output_dir)
    log.info("Node 1 - Cleaning completed successfully!")

if __name__ == "__main__":
    main()
