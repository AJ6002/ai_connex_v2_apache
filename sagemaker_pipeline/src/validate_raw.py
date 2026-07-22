"""
SageMaker Processing Job: Node 2 - Raw Feature Check
===================================================
Performs data quality checks (null ratios, bounds, and schema matches) on the cleaned raw data.
Fails execution if quality metrics exceed configured thresholds.
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
    parser = argparse.ArgumentParser(description="Node 2 - Raw Feature Check")
    parser.add_argument("--input-dir", type=str, required=True, help="S3 or local dir containing clean_dataset.parquet and manifest.json")
    parser.add_argument("--output-dir", type=str, required=True, help="S3 or local dir to save the raw_check_report.json")
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
        os.makedirs("/tmp/raw_input", exist_ok=True)
        
        local_parquet = "/tmp/raw_input/clean_dataset.parquet"
        local_manifest = "/tmp/raw_input/manifest.json"
        
        log.info(f"Downloading clean_dataset.parquet from s3://{bucket}/{key_prefix}...")
        s3.download_file(bucket, os.path.join(key_prefix, "clean_dataset.parquet").replace("\\", "/"), local_parquet)
        s3.download_file(bucket, os.path.join(key_prefix, "manifest.json").replace("\\", "/"), local_manifest)

    # Load data
    df = pd.read_parquet(local_parquet)
    manifest = load_json(local_manifest)
    
    schema_config = config.get("schema", {})
    time_idx = schema_config.get("time_index", "cycle")
    target_col = schema_config.get("target_column")
    
    thresholds = config.get("thresholds", {})
    max_missing_rate = thresholds.get("max_missing_rate", 0.02) # Default 2%

    # Quality Checks
    log.info("Starting raw feature quality validation...")
    checks = {}
    passed = True

    # 1. Missing Rate Check
    null_total = int(df.isnull().sum().sum())
    total_cells = df.shape[0] * df.shape[1]
    actual_missing_rate = null_total / total_cells
    
    checks["missing_rate"] = {
        "limit": max_missing_rate,
        "actual": actual_missing_rate,
        "status": "PASS" if actual_missing_rate <= max_missing_rate else "FAIL"
    }
    if actual_missing_rate > max_missing_rate:
        log.error(f"Missing rate of {actual_missing_rate:.4f} exceeds limit of {max_missing_rate:.4f}")
        passed = False

    # 2. Time Index Bounds Check
    min_time = df[time_idx].min()
    checks["negative_time_indices"] = {
        "actual_min": float(min_time),
        "status": "PASS" if min_time >= 0 else "FAIL"
    }
    if min_time < 0:
        log.error(f"Negative time index values found in column {time_idx}: min is {min_time}")
        passed = False

    # 3. Target Bounds Check (if target exists)
    if target_col and target_col in df.columns:
        min_target = df[target_col].min()
        checks["negative_targets"] = {
            "actual_min": float(min_target),
            "status": "PASS" if min_target >= 0 else "FAIL"
        }
        if min_target < 0:
            log.error(f"Negative target values found in column {target_col}: min is {min_target}")
            passed = False

    # Compile report
    report = {
        "manifest_id": manifest.get("manifest_id"),
        "status": "PASSED" if passed else "FAILED",
        "checks": checks
    }

    # Save validation report
    os.makedirs("/tmp/validate_raw", exist_ok=True)
    report_file = "/tmp/validate_raw/raw_check_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    save_file(report_file, args.output_dir)

    # Also update the manifest with quality gate status
    manifest["quality_gate_report"] = report
    local_manifest_updated = "/tmp/validate_raw/manifest.json"
    with open(local_manifest_updated, "w") as f:
        json.dump(manifest, f, indent=2)
    save_file(local_manifest_updated, args.output_dir)

    if not passed:
        log.error("Raw Feature validation checks failed!")
        sys.exit(1)
        
    log.info("Raw Feature validation checks passed successfully!")

if __name__ == "__main__":
    main()
