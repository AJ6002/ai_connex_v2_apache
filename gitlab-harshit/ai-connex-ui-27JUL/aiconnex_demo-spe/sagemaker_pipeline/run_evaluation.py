"""
Script to trigger the SageMaker Evaluation Job using SageMaker Local Mode.
Runs evaluate.py via local Docker, reading inputs from S3 and uploading metrics back to S3.
"""

import sagemaker
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.local import LocalSession

def main():
    # Initialize local session
    local_session = LocalSession()
    local_session.config = {'local': {'local_code': True}}
    
    # The role
    role = "arn:aws:iam::471112576437:role/service-role/AmazonSageMakerUserIAMExecutionRole_ce175b72"
    
    # S3 paths for inputs and output
    # Using the exact S3 URI of your successfully generated model.tar.gz
    model_s3_uri = "s3://aiconnex-cleaned/industrial/v1/preprocessed/model/sagemaker-scikit-learn-2026-07-15-06-33-01-995/output/model.tar.gz"
    val_data_s3_uri = "s3://aiconnex-cleaned/industrial/v1/preprocessed/val/"
    output_s3_uri = "s3://aiconnex-cleaned/industrial/v1/preprocessed/evaluation/"
    
    print("Initializing SageMaker SKLearnProcessor in LOCAL mode...")
    processor = SKLearnProcessor(
        framework_version="1.2-1",
        role=role,
        instance_count=1,
        instance_type="local",
        sagemaker_session=local_session
    )
    
    print("Running the Evaluation Job locally...")
    processor.run(
        code="sagemaker_pipeline/src/evaluate.py",
        inputs=[
            ProcessingInput(source=model_s3_uri, destination="/opt/ml/processing/model"),
            ProcessingInput(source=val_data_s3_uri, destination="/opt/ml/processing/test")
        ],
        outputs=[
            ProcessingOutput(source="/opt/ml/processing/evaluation", destination=output_s3_uri)
        ],
        arguments=[
            "--model-path", "/opt/ml/processing/model",
            "--test-path", "/opt/ml/processing/test",
            "--output-path", "/opt/ml/processing/evaluation"
        ]
    )
    print("\nSUCCESS! Evaluation completed and metrics uploaded to S3.")

if __name__ == "__main__":
    main()
