"""
Script to trigger the SageMaker Training Job using SageMaker Local Mode.
Bypasses the AWS account 0-instance quota limit by running the training container locally via Docker.
"""

import sagemaker
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.local import LocalSession

def main():
    # Initialize a SageMaker LocalSession to run the job in local Docker
    # but still interact with S3.
    local_session = LocalSession()
    local_session.config = {'local': {'local_code': True}}
    
    # The role
    role = "arn:aws:iam::471112576437:role/service-role/AmazonSageMakerUserIAMExecutionRole_ce175b72"
    
    # Target S3 path for the final model artifact
    output_path = "s3://aiconnex-cleaned/industrial/v1/preprocessed/model/"
    
    print("Initializing SageMaker SKLearn Estimator in LOCAL mode...")
    estimator = SKLearn(
        entry_point="train.py",
        source_dir="sagemaker_pipeline/src",
        role=role,
        instance_count=1,
        instance_type="local",  # <-- Local mode runs on your local Docker daemon
        framework_version="1.2-1",
        sagemaker_session=local_session,
        output_path=output_path,
        hyperparameters={
            "n-estimators": 100
        }
    )
    
    print("Running the Training Job locally...")
    # Read the data directly from S3
    estimator.fit(
        inputs={
            "train": "s3://aiconnex-cleaned/industrial/v1/preprocessed/train/",
            "val": "s3://aiconnex-cleaned/industrial/v1/preprocessed/val/"
        }
    )
    
    print("\nSUCCESS! Local training job completed and model uploaded to S3.")

if __name__ == "__main__":
    main()
