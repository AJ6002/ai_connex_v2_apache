"""
SageMaker Processing Job: Node 10 - Robustness & Stress Testing
==============================================================
Stress-tests the model by injecting random Gaussian noise/jitter into features
to verify prediction stability under sensor degradation.
"""

import os
import sys
import json
import argparse
import logging
import warnings
import pickle
import tarfile
import numpy as np
import pandas as pd
import boto3
from urllib.parse import urlparse
import sklearn.metrics

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Node 10 - Robustness & Stress Testing")
    parser.add_argument("--model-path", type=str, required=True, help="S3 or local path to model.tar.gz")
    parser.add_argument("--test-path", type=str, required=True, help="S3 or local path to test_engineered.parquet")
    parser.add_argument("--output-dir", type=str, required=True, help="S3 or local dir to save reports")
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

def load_pkl_model(model_path: str):
    """Helper to load a pickle model from S3 or local path."""
    os.makedirs("/tmp/stress_model", exist_ok=True)
    local_tar = model_path
    
    if model_path.startswith("s3://"):
        parsed = urlparse(model_path)
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        s3 = boto3.client('s3')
        local_tar = "/tmp/stress_model/model.tar.gz"
        s3.download_file(bucket, key, local_tar)

    extract_dir = "/tmp/stress_model/extracted"
    os.makedirs(extract_dir, exist_ok=True)
    
    with tarfile.open(local_tar, "r:gz") as tar:
        tar.extractall(extract_dir)
        
    extracted_files = []
    for root, _, files in os.walk(extract_dir):
        for f in files:
            extracted_files.append(os.path.join(root, f))
            
    pkl_files = [f for f in extracted_files if f.endswith(".pkl")]
    if not pkl_files:
        raise FileNotFoundError("Could not find model.pkl inside extracted archive")
        
    with open(pkl_files[0], "rb") as f:
        return pickle.load(f)

def main():
    args = parse_args()
    
    # Load manifest locally
    local_manifest = os.path.join(args.manifest_dir, "manifest.json")
    if args.manifest_dir.startswith("s3://"):
        os.makedirs("/tmp/stress_input", exist_ok=True)
        s3 = boto3.client('s3')
        p_man = urlparse(args.manifest_dir)
        s3.download_file(p_man.netloc, os.path.join(p_man.path.lstrip('/'), "manifest.json").replace("\\", "/"), "/tmp/stress_input/manifest.json")
        local_manifest = "/tmp/stress_input/manifest.json"

    manifest = load_json(local_manifest)
    features = manifest["schema"]["final_features"]
    target_col = manifest["schema"]["target_column"]
    
    routing = manifest.get("routing_decision", {})
    problem_type = routing.get("problem_type", "regression")
    
    # Download and load test split
    local_test = args.test_path
    if args.test_path.startswith("s3://"):
        os.makedirs("/tmp/stress_input", exist_ok=True)
        s3 = boto3.client('s3')
        p_test = urlparse(args.test_path)
        
        file_key = p_test.path.lstrip('/')
        if not file_key.endswith(".parquet"):
            file_key = os.path.join(file_key, "test_engineered.parquet").replace("\\", "/")
            
        local_test = "/tmp/stress_input/test_engineered.parquet"
        s3.download_file(p_test.netloc, file_key, local_test)

    df_test = pd.read_parquet(local_test)
    X_test = df_test[features].fillna(0)

    # Load model
    model = load_pkl_model(args.model_path)
    
    log.info("Running baseline predictions...")
    preds_baseline = model.predict(X_test)
    
    # Inject Gaussian Noise (jitter)
    log.info("Injecting 5% Gaussian noise into continuous features...")
    np.random.seed(42)
    X_noise = X_test.copy()
    
    for feat in features:
        # Standard deviation of the feature
        std_val = X_test[feat].std()
        if std_val > 0:
            noise = np.random.normal(0, 0.05 * std_val, size=X_test.shape[0])
            X_noise[feat] = X_noise[feat] + noise

    log.info("Running predictions on perturbed dataset...")
    preds_perturbed = model.predict(X_noise)

    passed = True
    degradation = 0.0

    if problem_type == "regression":
        y_test = df_test[target_col].fillna(0)
        rmse_base = sklearn.metrics.mean_squared_error(y_test, preds_baseline, squared=False)
        rmse_noise = sklearn.metrics.mean_squared_error(y_test, preds_perturbed, squared=False)
        
        # Calculate relative increase in RMSE
        degradation = (rmse_noise - rmse_base) / rmse_base
        log.info(f"  Baseline RMSE:  {rmse_base:.4f}")
        log.info(f"  Perturbed RMSE: {rmse_noise:.4f}")
        log.info(f"  RMSE Degradation: {degradation * 100:.2f}%")
        
        if degradation > 0.20: # Fails if RMSE increases by more than 20%
            passed = False
            log.error("Model is highly sensitive to input noise! Failing robustness check.")

    elif problem_type == "anomaly" and target_col and target_col in df_test.columns:
        y_test = df_test[target_col].fillna(0)
        
        y_pred_base = np.where(preds_baseline == -1, 1, 0)
        y_pred_noise = np.where(preds_perturbed == -1, 1, 0)
        
        f1_base = sklearn.metrics.f1_score(y_test, y_pred_base, zero_division=0)
        f1_noise = sklearn.metrics.f1_score(y_test, y_pred_noise, zero_division=0)
        
        # Calculate relative drop in F1-score
        degradation = (f1_base - f1_noise) / (f1_base if f1_base > 0 else 1)
        log.info(f"  Baseline F1-Score:  {f1_base:.4f}")
        log.info(f"  Perturbed F1-Score: {f1_noise:.4f}")
        log.info(f"  F1 Degradation: {degradation * 100:.2f}%")
        
        if degradation > 0.20: # Fails if F1 drops by more than 20%
            passed = False
            log.error("Model is highly sensitive to input noise! Failing robustness check.")

    report = {
        "manifest_id": manifest.get("manifest_id"),
        "status": "PASSED" if passed else "FAILED",
        "degradation_rate": float(degradation),
        "checks": {
            "noise_level_pct": 5.0,
            "max_allowed_degradation": 0.20,
            "actual_degradation": float(degradation),
            "passed": passed
        }
    }

    # Save report
    os.makedirs("/tmp/stress_out", exist_ok=True)
    report_file = "/tmp/stress_out/robustness_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    save_file(report_file, args.output_dir)

    # Update manifest
    if "quality_gate_report" not in manifest:
        manifest["quality_gate_report"] = {}
    manifest["quality_gate_report"]["robustness_checks"] = report
    local_manifest_updated = "/tmp/stress_out/manifest.json"
    with open(local_manifest_updated, "w") as f:
        json.dump(manifest, f, indent=2)
    save_file(local_manifest_updated, args.output_dir)

    log.info("Node 10 - Robustness & Stress testing completed successfully!")

if __name__ == "__main__":
    main()
