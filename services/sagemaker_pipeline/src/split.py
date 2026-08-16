"""
SageMaker Processing Job: Node 3 - Time-Series Splitter
======================================================
Performs chronological, group-based splitting on identifier (e.g. engine ID)
to prevent data leakage in time-series training.
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
    parser = argparse.ArgumentParser(description="Node 3 - Time-Series Splitter")
    parser.add_argument("--input-dir", type=str, required=True, help="S3 or local dir containing clean_dataset.parquet and manifest.json")
    parser.add_argument("--output-dir", type=str, required=True, help="S3 or local dir to write splits")
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

    # Resolve local path for clean_dataset
    local_parquet = os.path.join(args.input_dir, "clean_dataset.parquet")
    local_manifest = os.path.join(args.input_dir, "manifest.json")
    
    # If S3 paths, download them locally
    if args.input_dir.startswith("s3://"):
        parsed = urlparse(args.input_dir)
        bucket = parsed.netloc
        key_prefix = parsed.path.lstrip('/')
        
        s3 = boto3.client('s3')
        os.makedirs("/tmp/split_input", exist_ok=True)
        
        local_parquet = "/tmp/split_input/clean_dataset.parquet"
        local_manifest = "/tmp/split_input/manifest.json"
        
        log.info(f"Downloading clean_dataset.parquet from s3://{bucket}/{key_prefix}...")
        s3.download_file(bucket, os.path.join(key_prefix, "clean_dataset.parquet").replace("\\", "/"), local_parquet)
        s3.download_file(bucket, os.path.join(key_prefix, "manifest.json").replace("\\", "/"), local_manifest)

    # Load data
    df = pd.read_parquet(local_parquet)
    manifest = load_json(local_manifest)
    
    schema_config = config.get("schema", {})
    identifier = schema_config.get("identifier", "global_engine_id")
    
    # Group-based chronological split (preserving full time series per engine)
    unique_ids = df[identifier].unique()
    
    # Sort them to keep splitting chronological and deterministic
    unique_ids = sorted(unique_ids)
    
    n_total = len(unique_ids)
    train_end = int(n_total * 0.70)
    val_end = int(n_total * 0.85)
    
    train_ids = unique_ids[:train_end]
    val_ids = unique_ids[train_end:val_end]
    test_ids = unique_ids[val_end:]
    
    train_df = df[df[identifier].isin(train_ids)].copy().reset_index(drop=True)
    val_df = df[df[identifier].isin(val_ids)].copy().reset_index(drop=True)
    test_df = df[df[identifier].isin(test_ids)].copy().reset_index(drop=True)
    
    log.info(f"Splitting dataset by {identifier}:")
    log.info(f"  Total entities: {n_total}")
    log.info(f"  Train: {len(train_ids)} entities -> {train_df.shape[0]:,} rows")
    log.info(f"  Val:   {len(val_ids)} entities -> {val_df.shape[0]:,} rows")
    log.info(f"  Test:  {len(test_ids)} entities -> {test_df.shape[0]:,} rows")

    # Save splits
    os.makedirs("/tmp/splits", exist_ok=True)
    
    train_path = "/tmp/splits/train.parquet"
    val_path = "/tmp/splits/val.parquet"
    test_path = "/tmp/splits/test.parquet"
    
    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    test_df.to_parquet(test_path, index=False)
    
    save_file(train_path, args.output_dir)
    save_file(val_path, args.output_dir)
    save_file(test_path, args.output_dir)

    # Update manifest split strategy
    manifest["split_strategy"] = {
        "method": "group_chronological",
        "split_ratio": {"train": 0.70, "validation": 0.15, "test": 0.15},
        "train_uri": os.path.join(args.output_dir, "train.parquet").replace("\\", "/"),
        "val_uri": os.path.join(args.output_dir, "val.parquet").replace("\\", "/"),
        "test_uri": os.path.join(args.output_dir, "test.parquet").replace("\\", "/"),
        "train_rows": int(train_df.shape[0]),
        "val_rows": int(val_df.shape[0]),
        "test_rows": int(test_df.shape[0])
    }

    local_manifest_updated = "/tmp/splits/manifest.json"
    with open(local_manifest_updated, "w") as f:
        json.dump(manifest, f, indent=2)
    save_file(local_manifest_updated, args.output_dir)
    
    log.info("Node 3 - Time-Series Splitting completed successfully!")

if __name__ == "__main__":
    main()
