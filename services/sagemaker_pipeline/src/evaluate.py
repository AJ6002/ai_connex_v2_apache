"""
SageMaker Processing Job: Node 8 - Performance Evaluation
========================================================
Extracts the trained model (handling nested tarballs) and evaluates it on the test set.
Calculates Regression metrics (R², RMSE, MAE) or Anomaly Detection metrics (F1, Precision, Recall).
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
    parser = argparse.ArgumentParser(description="Node 8 - Performance Evaluation")
    parser.add_argument("--model-path", type=str, required=True, help="S3 or local path to model.tar.gz")
    parser.add_argument("--test-path", type=str, required=True, help="S3 or local path to test_engineered.parquet")
    parser.add_argument("--output-path", type=str, required=True, help="S3 or local dir to write evaluation.json")
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
    """Helper to load a pickle model from S3 or local path.
    Handles SageMaker double-nested tarballs recursively."""
    os.makedirs("/tmp/eval_model", exist_ok=True)
    local_tar = model_path
    
    if model_path.startswith("s3://"):
        parsed = urlparse(model_path)
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        
        s3 = boto3.client('s3')
        local_tar = "/tmp/eval_model/model.tar.gz"
        log.info(f"Downloading model archive from: {model_path}")
        s3.download_file(bucket, key, local_tar)

    # Recursive extraction loop
    extract_dir = "/tmp/eval_model/extracted"
    os.makedirs(extract_dir, exist_ok=True)
    current_archive = local_tar
    
    for i in range(5):
        if not current_archive.endswith(".tar.gz"):
            break
        log.info(f"Extracting tarball layer {i+1}: {current_archive}")
        layer_dir = os.path.join(extract_dir, f"layer_{i}")
        os.makedirs(layer_dir, exist_ok=True)
        
        with tarfile.open(current_archive, "r:gz") as tar:
            tar.extractall(layer_dir)
            
        # Scan extracted files
        extracted_files = []
        for root, _, files in os.walk(layer_dir):
            for f in files:
                extracted_files.append(os.path.join(root, f))
                
        pkl_files = [f for f in extracted_files if f.endswith(".pkl")]
        if pkl_files:
            current_archive = pkl_files[0]
            break
            
        tar_files = [f for f in extracted_files if f.endswith(".tar.gz")]
        if tar_files:
            current_archive = tar_files[0]
            continue
            
        raise ValueError(f"No model.pkl or nested tar.gz found in layer {i+1}")

    log.info(f"Loading pickle model from: {current_archive}")
    with open(current_archive, "rb") as f:
        model = pickle.load(f)
    return model

def main():
    args = parse_args()
    
    # Load manifest locally
    local_manifest = os.path.join(args.manifest_dir, "manifest.json")
    if args.manifest_dir.startswith("s3://"):
        os.makedirs("/tmp/eval_input", exist_ok=True)
        s3 = boto3.client('s3')
        p_man = urlparse(args.manifest_dir)
        s3.download_file(p_man.netloc, os.path.join(p_man.path.lstrip('/'), "manifest.json").replace("\\", "/"), "/tmp/eval_input/manifest.json")
        local_manifest = "/tmp/eval_input/manifest.json"

    manifest = load_json(local_manifest)
    
    # Get configuration from manifest
    schema_config = manifest.get("schema", {})
    features = schema_config.get("final_features")
    target_col = schema_config.get("target_column")
    
    routing = manifest.get("routing_decision", {})
    problem_type = routing.get("problem_type", "regression")
    
    # Download and load test split
    local_test = args.test_path
    if args.test_path.startswith("s3://"):
        os.makedirs("/tmp/eval_input", exist_ok=True)
        s3 = boto3.client('s3')
        p_test = urlparse(args.test_path)
        
        # S3 path could be folder or direct file
        file_key = p_test.path.lstrip('/')
        if not file_key.endswith(".parquet"):
            file_key = os.path.join(file_key, "test_engineered.parquet").replace("\\", "/")
            
        local_test = "/tmp/eval_input/test_engineered.parquet"
        log.info(f"Downloading test split from s3://{p_test.netloc}/{file_key}...")
        s3.download_file(p_test.netloc, file_key, local_test)

    df_test = pd.read_parquet(local_test)
    X_test = df_test[features].fillna(0)

    # Load model
    model = load_pkl_model(args.model_path)

    log.info("Running evaluation predictions...")
    
    metrics = {}
    
    if problem_type == "regression":
        y_test = df_test[target_col].fillna(0)
        y_pred = model.predict(X_test)
        
        r2 = sklearn.metrics.r2_score(y_test, y_pred)
        rmse = sklearn.metrics.mean_squared_error(y_test, y_pred, squared=False)
        mae = sklearn.metrics.mean_absolute_error(y_test, y_pred)
        
        metrics = {
            "regression_metrics": {
                "r2": {"value": float(r2), "standard_name": "R2"},
                "rmse": {"value": float(rmse), "standard_name": "RMSE"},
                "mae": {"value": float(mae), "standard_name": "MAE"}
            }
        }
        log.info(f"Evaluation Metrics: R2={r2:.4f} | RMSE={rmse:.2f} | MAE={mae:.2f}")

    elif problem_type == "anomaly":
        # Predict returns 1 (normal) and -1 (anomaly)
        preds = model.predict(X_test)
        y_pred_binary = np.where(preds == -1, 1, 0)
        anomaly_rate = float(np.mean(y_pred_binary))
        
        metrics = {
            "anomaly_metrics": {
                "anomaly_rate": {"value": anomaly_rate, "standard_name": "AnomalyRate"}
            }
        }
        
        # If ground-truth labels exist in the dataset, calculate precision/recall
        if target_col and target_col in df_test.columns:
            y_test = df_test[target_col].fillna(0)
            f1 = sklearn.metrics.f1_score(y_test, y_pred_binary, zero_division=0)
            precision = sklearn.metrics.precision_score(y_test, y_pred_binary, zero_division=0)
            recall = sklearn.metrics.recall_score(y_test, y_pred_binary, zero_division=0)
            
            metrics["anomaly_metrics"].update({
                "f1": {"value": float(f1), "standard_name": "F1"},
                "precision": {"value": float(precision), "standard_name": "Precision"},
                "recall": {"value": float(recall), "standard_name": "Recall"}
            })
            log.info(f"Anomaly Metrics: F1={f1:.4f} | Precision={precision:.4f} | Recall={recall:.4f}")
        else:
            log.info(f"Anomaly Metrics: Anomaly Rate={anomaly_rate:.4f} (No ground truth labels provided)")

    # Save evaluation metrics JSON (SageMaker standard format)
    os.makedirs("/tmp/eval_out", exist_ok=True)
    local_eval_file = "/tmp/eval_out/evaluation.json"
    with open(local_eval_file, "w") as f:
        json.dump(metrics, f, indent=2)
    save_file(local_eval_file, args.output_path)

    # Update manifest
    manifest["evaluation"] = metrics
    local_manifest_updated = "/tmp/eval_out/manifest.json"
    with open(local_manifest_updated, "w") as f:
        json.dump(manifest, f, indent=2)
    save_file(local_manifest_updated, args.output_path)

    log.info("Node 8 - Performance Evaluation completed successfully!")

if __name__ == "__main__":
    main()
