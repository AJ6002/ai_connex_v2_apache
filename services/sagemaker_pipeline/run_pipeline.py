"""
SageMaker Pipeline Runner: Dynamic, 12-Node Pipeline Upsert & Run
"""

import os
import argparse
import json
import boto3
import sagemaker
from sagemaker.workflow.pipeline_context import LocalPipelineSession, PipelineSession
from pipeline.pipeline import get_pipeline

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--local', action='store_true', help='Run in SageMaker Local Mode')
    parser.add_argument('--cloud', action='store_true', default=True, help='Run in SageMaker Cloud Mode')
    parser.add_argument('--input-uri', type=str, default='s3://aiconnex-ml-pipeline/raw/clean_train.parquet', help='S3 input parquet path')
    parser.add_argument('--config-uri', type=str, default='s3://aiconnex-ml-pipeline/config/config.json', help='S3 config JSON path')
    parser.add_argument('--role', type=str, default='arn:aws:iam::507044084046:role/aiconnex-sagemaker-role', help='AWS IAM Role ARN')
    return parser.parse_known_args()[0]

def main():
    args = parse_args()
    
    is_local = args.local and not args.cloud
    
    if is_local:
        print("Initializing pipeline in SageMaker LOCAL mode...")
        pipeline_session = LocalPipelineSession()
        role = args.role
        input_uri = args.input_uri
        config_uri = args.config_uri
    else:
        print("Initializing pipeline in SageMaker CLOUD mode...")
        pipeline_session = PipelineSession()
        role = args.role
        input_uri = args.input_uri
        config_uri = args.config_uri
        
        print(f"Cloud Role: {role}")
        print(f"Cloud Input URI: {input_uri}")
        print(f"Cloud Config URI: {config_uri}")
        
    # Create pipeline instance using the updated get_pipeline signature
    pipeline = get_pipeline(
        pipeline_session=pipeline_session,
        role=role,
        input_data_uri=input_uri,
        config_uri=config_uri,
        default_bucket="aiconnex-ml-pipeline"
    )
    
    print("Upserting pipeline definition in SageMaker...")
    pipeline.upsert(role_arn=role)
    
    print("Starting pipeline execution...")
    execution = pipeline.start()
    
    if not is_local:
        print(f"Pipeline Execution ARN: {execution.arn}")
        print("Pipeline triggered in the cloud successfully!")
    else:
        print("Pipeline execution completed locally.")

if __name__ == "__main__":
    main()
