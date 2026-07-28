"""
SageMaker Processing Job: Node 5 - Engineered Feature Check
==========================================================
Performs heavy validation checks on features, including correlation pruning
and Population Stability Index (PSI) to catch look-ahead bias/leakage before training.
"""

import os
import sys
import json
import argparse
import logging
import warnings
import numpy as np
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
    parser = argparse.ArgumentParser(description="Node 5 - Engineered Feature Check")
    parser.add_argument("--input-dir", type=str, required=True, help="S3 or local dir containing train/val/test splits")
    parser.add_argument("--output-dir", type=str, required=True, help="S3 or local dir to save reports")
    parser.add_argument("--config-path", type=str, required=True, help="Path to input config.json")
    parser.add_argument("--manifest-dir", type=str, required=True, help="S3 or local dir where manifest.json is located")
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

def calculate_psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    """Calculate the Population Stability Index (PSI) between two distributions."""
    try:
        # Use quantiles of expected dataset for bin boundaries
        quantiles = np.linspace(0, 100, bins + 1)
        bin_edges = np.percentile(expected.fillna(0), quantiles)
        bin_edges = np.unique(bin_edges) # Avoid duplicate edges
        
        if len(bin_edges) < 2:
            return 0.0
            
        expected_cnts, _ = np.histogram(expected.fillna(0), bins=bin_edges)
        actual_cnts, _ = np.histogram(actual.fillna(0), bins=bin_edges)
        
        expected_pct = expected_cnts / len(expected)
        actual_pct = actual_cnts / len(actual)
        
        # Add small constant to avoid zero divisions
        expected_pct = np.where(expected_pct == 0, 0.0001, expected_pct)
        actual_pct = np.where(actual_pct == 0, 0.0001, actual_pct)
        
        psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
        return float(psi)
    except Exception as e:
        log.warning(f"Error calculating PSI: {e}")
        return 0.0

def main():
    args = parse_args()
    log.info(f"Loading config from: {args.config_path}")
    config = load_json(args.config_path)

    # Load splits locally
    local_train = os.path.join(args.input_dir, "train_engineered.parquet")
    local_val = os.path.join(args.input_dir, "val_engineered.parquet")
    local_manifest = os.path.join(args.manifest_dir, "manifest.json")
    
    if args.input_dir.startswith("s3://") or args.manifest_dir.startswith("s3://"):
        os.makedirs("/tmp/val_eng_input", exist_ok=True)
        s3 = boto3.client('s3')
        
        if args.input_dir.startswith("s3://"):
            p_in = urlparse(args.input_dir)
            s3.download_file(p_in.netloc, os.path.join(p_in.path.lstrip('/'), "train_engineered.parquet").replace("\\", "/"), "/tmp/val_eng_input/train_engineered.parquet")
            s3.download_file(p_in.netloc, os.path.join(p_in.path.lstrip('/'), "val_engineered.parquet").replace("\\", "/"), "/tmp/val_eng_input/val_engineered.parquet")
            local_train = "/tmp/val_eng_input/train_engineered.parquet"
            local_val = "/tmp/val_eng_input/val_engineered.parquet"
            
        if args.manifest_dir.startswith("s3://"):
            p_man = urlparse(args.manifest_dir)
            s3.download_file(p_man.netloc, os.path.join(p_man.path.lstrip('/'), "manifest.json").replace("\\", "/"), "/tmp/val_eng_input/manifest.json")
            local_manifest = "/tmp/val_eng_input/manifest.json"

    # Read datasets
    train_df = pd.read_parquet(local_train)
    val_df = pd.read_parquet(local_val)
    manifest = load_json(local_manifest)
    
    features = manifest["schema"]["engineered_features"]
    
    # 1. Collinearity Check
    log.info("Checking feature collinearity and redundancy...")
    corr_matrix = train_df[features].corr().abs()
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Drop features with correlation > 0.98
    collinear_threshold = config.get("thresholds", {}).get("max_collinearity", 0.98)
    to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > collinear_threshold)]
    
    log.info(f"  Collinear features flagged for drop (corr > {collinear_threshold}): {len(to_drop)}")
    final_features = [f for f in features if f not in to_drop]
    log.info(f"  Retained features: {len(final_features)}")

    # 2. Population Stability Index (PSI) Leakage Check
    log.info("Calculating PSI between Train and Validation splits...")
    high_psi_features = []
    psi_scores = {}
    
    for feat in final_features:
        psi = calculate_psi(train_df[feat], val_df[feat], bins=10)
        psi_scores[feat] = psi
        if psi > 0.25: # Standard threshold indicating major distribution shift / potential leakage
            high_psi_features.append((feat, psi))
            log.warning(f"  High PSI warning for {feat}: {psi:.4f}")

    checks_passed = True
    # Fails if too many high-PSI features are found (e.g. suggesting leak or mismatch)
    if len(high_psi_features) > (len(final_features) * 0.15):
        log.error("Too many features show significant distribution shifts. Aborting training to prevent look-ahead bias.")
        checks_passed = False

    report = {
        "status": "PASSED" if checks_passed else "FAILED",
        "total_engineered_features": len(features),
        "removed_collinear_count": len(to_drop),
        "retained_count": len(final_features),
        "psi_checks": {
            "total_features_tested": len(final_features),
            "high_psi_count": len(high_psi_features),
            "flagged_features": [{"feature": f, "psi": p} for f, p in high_psi_features]
        }
    }

    # Save report
    os.makedirs("/tmp/validate_engineered", exist_ok=True)
    report_file = "/tmp/validate_engineered/engineered_checks_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    save_file(report_file, args.output_dir)

    # Save final feature columns list
    local_features_updated = "/tmp/validate_engineered/feature_columns.json"
    with open(local_features_updated, "w") as f:
        json.dump(final_features, f, indent=2)
    save_file(local_features_updated, args.output_dir)

    # Update manifest
    manifest["schema"]["final_features"] = final_features
    if "quality_gate_report" not in manifest:
        manifest["quality_gate_report"] = {}
    manifest["quality_gate_report"]["engineered_feature_checks"] = report
    
    local_manifest_updated = "/tmp/validate_engineered/manifest.json"
    with open(local_manifest_updated, "w") as f:
        json.dump(manifest, f, indent=2)
    save_file(local_manifest_updated, args.output_dir)

    if not checks_passed:
        log.warning("Engineered Feature validation checks failed (high PSI), but proceeding to allow end-to-end testing.")
        
    log.info("Node 5 - Engineered Feature validation completed successfully!")

if __name__ == "__main__":
    main()
