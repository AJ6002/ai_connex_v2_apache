"""
SageMaker Processing Job: Node 11 - Model Registry
==================================================
Validates final metrics against thresholds and registers the model in the SageMaker Model Registry.
"""

import os
import sys
import json
import argparse
import logging
import warnings
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
    parser = argparse.ArgumentParser(description="Node 11 - Model Registry")
    parser.add_argument("--evaluation-path", type=str, required=True, help="S3 or local path to evaluation.json")
    parser.add_argument("--model-path", type=str, required=True, help="S3 or local path to model.tar.gz")
    parser.add_argument("--model-package-group", type=str, required=True, help="Model package group name")
    parser.add_argument("--min-r2", type=float, default=0.55, help="Minimum R2 threshold for regression")
    parser.add_argument("--min-f1", type=float, default=0.50, help="Minimum F1 threshold for anomaly detection")
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

def main():
    args = parse_args()
    sm = boto3.client('sagemaker')
    
    # Load manifest locally
    local_manifest = os.path.join(args.manifest_dir, "manifest.json")
    if args.manifest_dir.startswith("s3://"):
        os.makedirs("/tmp/register_input", exist_ok=True)
        s3 = boto3.client('s3')
        p_man = urlparse(args.manifest_dir)
        s3.download_file(p_man.netloc, os.path.join(p_man.path.lstrip('/'), "manifest.json").replace("\\", "/"), "/tmp/register_input/manifest.json")
        local_manifest = "/tmp/register_input/manifest.json"

    manifest = load_json(local_manifest)
    routing = manifest.get("routing_decision", {})
    problem_type = routing.get("problem_type", "regression")

    # Load metrics
    metrics = load_json(args.evaluation_path)
    
    passed = True
    metric_str = ""

    if problem_type == "regression":
        r2 = metrics['regression_metrics']['r2']['value']
        rmse = metrics['regression_metrics']['rmse']['value']
        metric_str = f"R2: {r2:.4f}, RMSE: {rmse:.4f}"
        
        log.info(f"Validating Quality Gate: Actual R2 ({r2:.4f}) vs Required Min R2 ({args.min_r2:.4f})")
        if r2 < args.min_r2:
            passed = False
            log.error(f"Quality gate failed: R2 ({r2:.4f}) is below minimum of {args.min_r2:.4f}")
            
    elif problem_type == "anomaly":
        # Check if F1 exists
        anomaly_metrics = metrics.get("anomaly_metrics", {})
        if "f1" in anomaly_metrics:
            f1 = anomaly_metrics["f1"]["value"]
            metric_str = f"F1: {f1:.4f}"
            log.info(f"Validating Quality Gate: Actual F1 ({f1:.4f}) vs Required Min F1 ({args.min_f1:.4f})")
            if f1 < args.min_f1:
                passed = False
                log.error(f"Quality gate failed: F1 ({f1:.4f}) is below minimum of {args.min_f1:.4f}")
        else:
            anomaly_rate = anomaly_metrics.get("anomaly_rate", {}).get("value", 0.0)
            metric_str = f"Anomaly Rate: {anomaly_rate:.4f}"
            log.info("Anomaly detection run has no ground truth labels. Skipping quality gate check.")

    if not passed:
        sys.exit(1)
        
    log.info("Quality gate passed! Registering model package...")

    # Ensure Model Package Group exists
    try:
        sm.create_model_package_group(
            ModelPackageGroupName=args.model_package_group,
            ModelPackageGroupDescription="Aiconnex Turbofan Prediction Models"
        )
        log.info(f"Created new Model Package Group: {args.model_package_group}")
    except sm.exceptions.ClientError as e:
        if "ValidationException" in str(e) and "already exists" in str(e):
            log.info(f"Model Package Group {args.model_package_group} already exists.")
        else:
            raise e

    # Register the model package under 'PendingManualApproval'
    container_def = {
        "Image": "720646828776.dkr.ecr.ap-south-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3",
        "ModelDataUrl": args.model_path,
        "Environment": {
            "SAGEMAKER_PROGRAM": "train.py"
        }
    }
    
    register_response = sm.create_model_package(
        ModelPackageGroupName=args.model_package_group,
        ModelPackageDescription=f"Model registered automatically. {metric_str}",
        InferenceSpecification={
            "Containers": [container_def],
            "SupportedTransformInstanceTypes": ["ml.m5.large"],
            "SupportedRealtimeInferenceInstanceTypes": ["ml.m5.large"],
            "SupportedContentTypes": ["text/csv"],
            "SupportedResponseMIMETypes": ["text/csv"]
        },
        ModelApprovalStatus="PendingManualApproval"
    )

    model_package_arn = register_response["ModelPackageArn"]
    log.info("=" * 60)
    log.info("MODEL REGISTRATION SUCCESSFUL:")
    log.info(f"  ModelPackageArn: {model_package_arn}")
    log.info("=" * 60)

    # Update manifest
    manifest["registry"] = {
        "status": "REGISTERED",
        "model_package_arn": model_package_arn,
        "model_package_group": args.model_package_group,
        "metrics_summary": metric_str
    }
    local_manifest_updated = "/tmp/register_input/manifest.json"
    with open(local_manifest_updated, "w") as f:
        json.dump(manifest, f, indent=2)
    save_file(local_manifest_updated, args.manifest_dir)

if __name__ == "__main__":
    main()
