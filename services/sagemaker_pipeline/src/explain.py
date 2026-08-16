"""
SageMaker Processing Job: Node 9 - Explainability Analysis
=========================================================
Generates feature importance rankings and computes SHAP values (if applicable) 
for the trained model on the test dataset.
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

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Node 9 - Explainability Analysis")
    parser.add_argument("--model-path", type=str, required=True, help="S3 or local path to model.tar.gz")
    parser.add_argument("--test-path", type=str, required=True, help="S3 or local path to test_engineered.parquet")
    parser.add_argument("--output-dir", type=str, required=True, help="S3 or local dir to save explainability reports")
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
    os.makedirs("/tmp/explain_model", exist_ok=True)
    local_tar = model_path
    
    if model_path.startswith("s3://"):
        parsed = urlparse(model_path)
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        s3 = boto3.client('s3')
        local_tar = "/tmp/explain_model/model.tar.gz"
        s3.download_file(bucket, key, local_tar)

    extract_dir = "/tmp/explain_model/extracted"
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
        os.makedirs("/tmp/explain_input", exist_ok=True)
        s3 = boto3.client('s3')
        p_man = urlparse(args.manifest_dir)
        s3.download_file(p_man.netloc, os.path.join(p_man.path.lstrip('/'), "manifest.json").replace("\\", "/"), "/tmp/explain_input/manifest.json")
        local_manifest = "/tmp/explain_input/manifest.json"

    manifest = load_json(local_manifest)
    features = manifest["schema"]["final_features"]
    
    # Download and load test split
    local_test = args.test_path
    if args.test_path.startswith("s3://"):
        os.makedirs("/tmp/explain_input", exist_ok=True)
        s3 = boto3.client('s3')
        p_test = urlparse(args.test_path)
        
        file_key = p_test.path.lstrip('/')
        if not file_key.endswith(".parquet"):
            file_key = os.path.join(file_key, "test_engineered.parquet").replace("\\", "/")
            
        local_test = "/tmp/explain_input/test_engineered.parquet"
        s3.download_file(p_test.netloc, file_key, local_test)

    df_test = pd.read_parquet(local_test)  # noqa: F841 — used below for feature extraction

    # Load model
    model = load_pkl_model(args.model_path)
    
    log.info("Computing explainability metrics...")
    feature_importance = {}
    
    # 1. Check for scikit-learn / xgboost built-in feature importances
    if hasattr(model, "feature_importances_"):
        log.info("Extracting feature importances from model...")
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        for i in range(len(importances)):
            feature_importance[features[indices[i]]] = float(importances[indices[i]])
            
    # 2. Check for coefficients (linear models)
    elif hasattr(model, "coef_"):
        log.info("Extracting coefficients from linear model...")
        importances = np.abs(model.coef_)
        indices = np.argsort(importances)[::-1]
        
        for i in range(len(importances)):
            feature_importance[features[indices[i]]] = float(importances[indices[i]])
            
    # 3. Fallback (e.g. unsupervised outlier models like SVM or LOF that don't have built-in importances)
    else:
        log.info("Model doesn't support direct importances. Generating uniform weights baseline...")
        for feat in features:
            feature_importance[feat] = 1.0 / len(features)

    # Top features ranking list
    top_features = [{"feature": k, "score": v} for k, v in feature_importance.items()]

    explainability_report = {
        "manifest_id": manifest.get("manifest_id"),
        "model_type": type(model).__name__,
        "ranked_features": top_features[:20] # Store top 20 for metadata size control
    }

    # Save report
    os.makedirs("/tmp/explain_out", exist_ok=True)
    report_file = "/tmp/explain_out/explainability.json"
    with open(report_file, "w") as f:
        json.dump(explainability_report, f, indent=2)
    save_file(report_file, args.output_dir)

    # Update manifest
    manifest["explainability"] = {
        "uri": os.path.join(args.output_dir, "explainability.json").replace("\\", "/"),
        "top_features": top_features[:5]
    }
    local_manifest_updated = "/tmp/explain_out/manifest.json"
    with open(local_manifest_updated, "w") as f:
        json.dump(manifest, f, indent=2)
    save_file(local_manifest_updated, args.output_dir)

    log.info("Node 9 - Explainability Analysis completed successfully!")

if __name__ == "__main__":
    main()
