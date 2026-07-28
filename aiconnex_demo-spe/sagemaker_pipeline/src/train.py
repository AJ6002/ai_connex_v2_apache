"""
SageMaker Processing Job: Node 6 - Baseline Model Training
=========================================================
Dynamically imports and trains the specified algorithm (Regression or Anomaly Detection)
from a central ALGORITHM_REGISTRY using configuration parameter injection.
"""

import os
import sys
import json
import argparse
import logging
import warnings
import pickle
import tarfile
import pandas as pd
import boto3
from urllib.parse import urlparse

# Scikit-learn & XGBoost algorithm registry
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.svm import OneClassSVM

try:
    import xgboost as xgb
except ImportError:
    import subprocess
    import sys
    print("XGBoost not found. Installing xgboost package in runtime container...")
    subprocess.run([sys.executable, "-m", "pip", "install", "xgboost>=1.7.0,<2.0.0"])
    import xgboost as xgb

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

ALGORITHM_REGISTRY = {
    "random_forest": RandomForestRegressor,
    "xgboost": xgb.XGBRegressor,
    "linear_regression": LinearRegression,
    "ridge": Ridge,
    "isolation_forest": IsolationForest,
    "one_class_svm": OneClassSVM
}

def parse_args():
    parser = argparse.ArgumentParser(description="Node 6 - Baseline Training")
    parser.add_argument("--input-dir", type=str, required=True, help="S3 or local dir containing train/val engineered splits")
    parser.add_argument("--output-dir", type=str, required=True, help="S3 or local dir to write model.tar.gz")
    parser.add_argument("--config-path", type=str, required=True, help="Path to input config.json")
    parser.add_argument("--manifest-dir", type=str, required=True, help="S3 or local dir where manifest.json is located")
    parser.add_argument("--n-estimators", type=int, default=None, help="Dynamic parameter override for n-estimators")
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

    # Load splits locally
    local_train = os.path.join(args.input_dir, "train_engineered.parquet")
    local_manifest = os.path.join(args.manifest_dir, "manifest.json")
    
    if args.input_dir.startswith("s3://") or args.manifest_dir.startswith("s3://"):
        os.makedirs("/tmp/train_input", exist_ok=True)
        s3 = boto3.client('s3')
        
        if args.input_dir.startswith("s3://"):
            p_in = urlparse(args.input_dir)
            s3.download_file(p_in.netloc, os.path.join(p_in.path.lstrip('/'), "train_engineered.parquet").replace("\\", "/"), "/tmp/train_input/train_engineered.parquet")
            local_train = "/tmp/train_input/train_engineered.parquet"
            
        if args.manifest_dir.startswith("s3://"):
            p_man = urlparse(args.manifest_dir)
            s3.download_file(p_man.netloc, os.path.join(p_man.path.lstrip('/'), "manifest.json").replace("\\", "/"), "/tmp/train_input/manifest.json")
            local_manifest = "/tmp/train_input/manifest.json"

    # Read datasets
    train_df = pd.read_parquet(local_train)
    manifest = load_json(local_manifest)
    
    # Retrieve dynamic features and labels
    schema_config = manifest.get("schema", {})
    features = schema_config.get("final_features")
    target_col = schema_config.get("target_column")
    
    routing = manifest.get("routing_decision", {})
    problem_type = routing.get("problem_type", "regression")
    algo_name = routing.get("algorithm", "random_forest")

    log.info("Preparing to train baseline model:")
    log.info(f"  Problem Type: {problem_type.upper()}")
    log.info(f"  Selected Algorithm: {algo_name}")
    log.info(f"  Feature Count: {len(features)}")

    # Verify algorithm exists in registry
    if algo_name not in ALGORITHM_REGISTRY:
        raise ValueError(f"Algorithm '{algo_name}' is not registered in ALGORITHM_REGISTRY. Available: {list(ALGORITHM_REGISTRY.keys())}")

    # Build hyperparameters block
    hyperparams = config.get("hyperparameters", {}).copy()
    if args.n_estimators is not None and "n_estimators" in hyperparams:
        log.info(f"Overriding n_estimators with command-line parameter: {args.n_estimators}")
        hyperparams["n_estimators"] = args.n_estimators

    # Instantiate model with filtered hyperparameters
    import inspect
    model_class = ALGORITHM_REGISTRY[algo_name]
    sig = inspect.signature(model_class.__init__)
    has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    if not has_kwargs:
        filtered_hyperparams = {k: v for k, v in hyperparams.items() if k in sig.parameters}
        log.info(f"Filtered hyperparameters for {model_class.__name__}: {filtered_hyperparams}")
    else:
        filtered_hyperparams = hyperparams
        
    model = model_class(**filtered_hyperparams)

    # Separate X and y
    X_train = train_df[features].fillna(0)
    
    if problem_type == "regression":
        y_train = train_df[target_col].fillna(0)
        log.info(f"Fitting {model_class.__name__} on features and target column '{target_col}'...")
        model.fit(X_train, y_train)
    elif problem_type == "anomaly":
        # Unsupervised models (e.g. Isolation Forest) only fit on features
        log.info(f"Fitting unsupervised {model_class.__name__} on features...")
        model.fit(X_train)

    log.info("Model fitting complete. Packaging artifacts...")

    # Save model artifact
    os.makedirs("/tmp/model_output", exist_ok=True)
    local_pkl = "/tmp/model_output/model.pkl"
    local_tar = "/tmp/model_output/model.tar.gz"
    
    with open(local_pkl, "wb") as f:
        pickle.dump(model, f)
        
    with tarfile.open(local_tar, "w:gz") as tar:
        tar.add(local_pkl, arcname="model.pkl")

    save_file(local_tar, args.output_dir)

    # Update manifest with model URI
    model_s3_uri = os.path.join(args.output_dir, "model.tar.gz").replace("\\", "/")
    manifest["models"] = {
        "baseline": {
            "uri": model_s3_uri,
            "algorithm": algo_name,
            "hyperparameters": hyperparams
        }
    }
    
    local_manifest_updated = "/tmp/model_output/manifest.json"
    with open(local_manifest_updated, "w") as f:
        json.dump(manifest, f, indent=2)
    save_file(local_manifest_updated, args.output_dir)

    log.info("Node 6 - Baseline Training completed successfully!")

if __name__ == "__main__":
    main()
