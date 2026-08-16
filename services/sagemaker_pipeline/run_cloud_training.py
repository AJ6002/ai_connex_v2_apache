"""
Script to trigger a REAL cloud SageMaker Training Job on the newly approved ml.m5.large instance.
"""

import sagemaker
from sagemaker.sklearn.estimator import SKLearn

def main():
    # Use a standard cloud session (not local)
    sagemaker_session = sagemaker.Session()
    
    # The role with S3 and Admin access
    role = "arn:aws:iam::471112576437:role/service-role/AmazonSageMakerUserIAMExecutionRole_ce175b72"
    
    # S3 output path
    output_path = "s3://aiconnex-cleaned/industrial/v1/preprocessed/model/"
    
    print("Initializing SageMaker SKLearn Estimator for CLOUD training...")
    estimator = SKLearn(
        entry_point="train.py",
        source_dir="sagemaker_pipeline/src",
        role=role,
        instance_count=1,
        instance_type="ml.m5.large",  # <-- Using your approved cloud instance
        framework_version="1.2-1",
        sagemaker_session=sagemaker_session,
        output_path=output_path,
        hyperparameters={
            "n-estimators": 100
        }
    )
    
    print("Triggering the Cloud Training Job in SageMaker...")
    estimator.fit(
        inputs={
            "train": "s3://aiconnex-cleaned/industrial/v1/preprocessed/train/",
            "val": "s3://aiconnex-cleaned/industrial/v1/preprocessed/val/"
        },
        wait=True  # This will stream the cloud training logs directly to your terminal
    )
    
    print("\nSUCCESS! Cloud training job completed.")

if __name__ == "__main__":
    main()
