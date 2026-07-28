"""
Lightweight script to validate the trained S3 model before evaluation runs.
Loads the model, extracts it, checks for integrity, and prints key parameters.
"""

import os
import tarfile
import pickle
import boto3
from urllib.parse import urlparse

# Glue context support
try:
    from awsglue.utils import getResolvedOptions  # noqa: F401
    IS_GLUE = True
except ImportError:
    IS_GLUE = False

def run_validation():
    # S3 path to the model
    model_s3_uri = "s3://aiconnex-cleaned/industrial/v1/preprocessed/model/sagemaker-scikit-learn-2026-07-15-06-33-01-995/output/model.tar.gz"
    
    print(f"Fetching model from S3: {model_s3_uri}")
    parsed = urlparse(model_s3_uri)
    bucket = parsed.netloc
    key = parsed.path.lstrip('/')
    
    local_tar = "/tmp/model.tar.gz"
    local_extract = "/tmp/extract"
    os.makedirs(local_extract, exist_ok=True)
    
    s3 = boto3.client('s3')
    s3.download_file(bucket, key, local_tar)
    print(f"Downloaded model tarball. Size: {os.path.getsize(local_tar)} bytes.")
    
    # Extract outer layer
    with tarfile.open(local_tar, "r:gz") as tar:
        tar.extractall(local_extract)
        
    extracted_files = os.listdir(local_extract)
    print(f"Extracted files from first layer: {extracted_files}")
    
    model_file = os.path.join(local_extract, "model.pkl")
    
    # Check for nested tarball (SageMaker local mode output)
    if "model.tar.gz" in extracted_files:
        print("Detected nested tarball. Extracting second layer...")
        nested_tar = os.path.join(local_extract, "model.tar.gz")
        nested_extract = "/tmp/extract_inner"
        os.makedirs(nested_extract, exist_ok=True)
        with tarfile.open(nested_tar, "r:gz") as tar:
            tar.extractall(nested_extract)
        model_file = os.path.join(nested_extract, "model.pkl")
        
    print(f"Loading model from {model_file} to verify serialization...")
    with open(model_file, "rb") as f:
        model = pickle.load(f)
        
    print("=" * 60)
    print("MODEL VALIDATION SUMMARY:")
    print(f"  Model Type: {type(model).__name__}")
    if hasattr(model, "n_estimators"):
        print(f"  n_estimators: {model.n_estimators}")
    if hasattr(model, "n_features_in_"):
        print(f"  Expected input features count: {model.n_features_in_}")
    print("=" * 60)
    print("Model validation completed successfully!")

if __name__ == "__main__":
    run_validation()
