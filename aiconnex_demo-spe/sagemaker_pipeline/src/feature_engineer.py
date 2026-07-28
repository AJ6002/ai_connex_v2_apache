"""
SageMaker Processing Job: Node 4 - Feature Engineering
=====================================================
Calculates rolling averages, lags, and fits standard scaling (fitted ONLY on train).
Applies the fitted scaling to all splits.
"""

import os
import sys
import json
import argparse
import logging
import warnings
import pickle
import pandas as pd
import boto3
from urllib.parse import urlparse
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Node 4 - Feature Engineering")
    parser.add_argument("--input-dir", type=str, required=True, help="S3 or local dir containing train/val/test splits")
    parser.add_argument("--output-dir", type=str, required=True, help="S3 or local dir to write engineered splits")
    parser.add_argument("--artifacts-dir", type=str, required=True, help="S3 or local dir to write scaler.pkl")
    parser.add_argument("--config-path", type=str, required=True, help="Path to input config.json")
    parser.add_argument("--manifest-dir", type=str, required=True, help="S3 or local dir where manifest.json is updated")
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

def process_features(df: pd.DataFrame, features: list, time_idx: str, identifier: str) -> pd.DataFrame:
    # Drop any pre-existing engineered columns to prevent duplicates on concat
    active_sensors = [s for s in features if df[s].std() > 0]
    cols_to_drop = []
    for window in [10, 20]:
        for col in active_sensors:
            cols_to_drop.append(f"{col}_roll_mean_{window}")
            cols_to_drop.append(f"{col}_roll_std_{window}")
    for lag in [1, 2]:
        for col in active_sensors:
            cols_to_drop.append(f"{col}_lag_{lag}_diff")
    cols_to_drop.append("time_standardized")
    
    existing_drops = [c for c in cols_to_drop if c in df.columns]
    if existing_drops:
        df = df.drop(columns=existing_drops)
        
    # 1. Standardized time cycle
    df['time_standardized'] = df[time_idx] / 300.0
    
    # 2. Rolling window features (window = 10, 20)
    rolling_dfs = []
    
    for window in [10, 20]:
        roll = df.groupby(identifier)[active_sensors].rolling(window=window, min_periods=1)
        
        mean_df = roll.mean().reset_index(level=0, drop=True)
        mean_df.columns = [f"{col}_roll_mean_{window}" for col in active_sensors]
        
        std_df = roll.std().reset_index(level=0, drop=True).fillna(0.0)
        std_df.columns = [f"{col}_roll_std_{window}" for col in active_sensors]
        
        rolling_dfs.extend([mean_df, std_df])
        
    # 3. Lag features (lags 1 & 2 differences)
    lag_dfs = []
    for lag in [1, 2]:
        lag_val = df.groupby(identifier)[active_sensors].shift(lag)
        diff_df = (df[active_sensors] - lag_val).fillna(0.0)
        diff_df.columns = [f"{col}_lag_{lag}_diff" for col in active_sensors]
        lag_dfs.append(diff_df)
        
    # Concatenate features
    engineered_df = pd.concat([df] + rolling_dfs + lag_dfs, axis=1)
    return engineered_df

def main():
    args = parse_args()
    log.info(f"Loading config from: {args.config_path}")
    config = load_json(args.config_path)

    # Load splits locally
    local_train = os.path.join(args.input_dir, "train.parquet")
    local_val = os.path.join(args.input_dir, "val.parquet")
    local_test = os.path.join(args.input_dir, "test.parquet")
    local_manifest = os.path.join(args.manifest_dir, "manifest.json")
    
    if args.input_dir.startswith("s3://") or args.manifest_dir.startswith("s3://"):
        os.makedirs("/tmp/fe_input", exist_ok=True)
        s3 = boto3.client('s3')
        
        if args.input_dir.startswith("s3://"):
            p_in = urlparse(args.input_dir)
            s3.download_file(p_in.netloc, os.path.join(p_in.path.lstrip('/'), "train.parquet").replace("\\", "/"), "/tmp/fe_input/train.parquet")
            s3.download_file(p_in.netloc, os.path.join(p_in.path.lstrip('/'), "val.parquet").replace("\\", "/"), "/tmp/fe_input/val.parquet")
            s3.download_file(p_in.netloc, os.path.join(p_in.path.lstrip('/'), "test.parquet").replace("\\", "/"), "/tmp/fe_input/test.parquet")
            local_train = "/tmp/fe_input/train.parquet"
            local_val = "/tmp/fe_input/val.parquet"
            local_test = "/tmp/fe_input/test.parquet"
            
        if args.manifest_dir.startswith("s3://"):
            p_man = urlparse(args.manifest_dir)
            s3.download_file(p_man.netloc, os.path.join(p_man.path.lstrip('/'), "manifest.json").replace("\\", "/"), "/tmp/fe_input/manifest.json")
            local_manifest = "/tmp/fe_input/manifest.json"

    # Read datasets
    train_df = pd.read_parquet(local_train)
    val_df = pd.read_parquet(local_val)
    test_df = pd.read_parquet(local_test)
    manifest = load_json(local_manifest)
    
    schema_config = config.get("schema", {})
    features = schema_config.get("features", [])
    time_idx = schema_config.get("time_index", "cycle")
    identifier = schema_config.get("identifier", "global_engine_id")
    target_col = schema_config.get("target_column")

    # Apply rolling & lag feature engineering
    log.info("Calculating rolling and lag features...")
    train_fe = process_features(train_df, features, time_idx, identifier)
    val_fe = process_features(val_df, features, time_idx, identifier)
    test_fe = process_features(test_df, features, time_idx, identifier)

    # Categorize engineered features
    exclude = [identifier, time_idx, target_col, "dataset_id", "fault_mode", "operating_condition"]
    continuous_features = [c for c in train_fe.columns if c not in exclude and pd.api.types.is_numeric_dtype(train_fe[c])]

    # Fit scaling transformer ONLY on train split
    log.info(f"Fitting StandardScaler on {len(continuous_features)} continuous features...")
    scaler = StandardScaler()
    train_fe[continuous_features] = scaler.fit_transform(train_fe[continuous_features].fillna(0))
    val_fe[continuous_features] = scaler.transform(val_fe[continuous_features].fillna(0))
    test_fe[continuous_features] = scaler.transform(test_fe[continuous_features].fillna(0))

    # Save artifact scaling object
    os.makedirs("/tmp/fe_artifacts", exist_ok=True)
    local_scaler_file = "/tmp/fe_artifacts/scaler.pkl"
    local_features_file = "/tmp/fe_artifacts/feature_columns.json"
    
    with open(local_scaler_file, "wb") as f:
        pickle.dump(scaler, f)
    with open(local_features_file, "w") as f:
        json.dump(continuous_features, f, indent=2)
        
    save_file(local_scaler_file, args.artifacts_dir)
    save_file(local_features_file, args.artifacts_dir)

    # Save engineered datasets
    os.makedirs("/tmp/fe_output", exist_ok=True)
    local_train_out = "/tmp/fe_output/train_engineered.parquet"
    local_val_out = "/tmp/fe_output/val_engineered.parquet"
    local_test_out = "/tmp/fe_output/test_engineered.parquet"
    
    train_fe.to_parquet(local_train_out, index=False)
    val_fe.to_parquet(local_val_out, index=False)
    test_fe.to_parquet(local_test_out, index=False)
    
    save_file(local_train_out, args.output_dir)
    save_file(local_val_out, args.output_dir)
    save_file(local_test_out, args.output_dir)

    # Update manifest
    manifest["preprocessing_applied"] = {
        "scaling": {"method": "StandardScaler", "fitted_on": "train_split"},
        "rolling_windows": ["10", "20"],
        "lags": ["1", "2"]
    }
    manifest["schema"]["engineered_features"] = continuous_features
    manifest["split_strategy"].update({
        "train_engineered_uri": os.path.join(args.output_dir, "train_engineered.parquet").replace("\\", "/"),
        "val_engineered_uri": os.path.join(args.output_dir, "val_engineered.parquet").replace("\\", "/"),
        "test_engineered_uri": os.path.join(args.output_dir, "test_engineered.parquet").replace("\\", "/"),
    })

    local_manifest_updated = "/tmp/fe_output/manifest.json"
    with open(local_manifest_updated, "w") as f:
        json.dump(manifest, f, indent=2)
    save_file(local_manifest_updated, args.output_dir)

    log.info("Node 4 - Feature Engineering completed successfully!")

if __name__ == "__main__":
    main()
