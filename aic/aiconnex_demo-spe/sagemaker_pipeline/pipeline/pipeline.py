"""
SageMaker Pipeline Definition: 12-Node Dynamic, Algorithm-Agnostic ML Pipeline
=============================================================================
Defines the sequential steps (Cleaning -> Checks -> Split -> Feature Eng ->
Checks -> Training -> HPO -> Eval -> Explain -> Stress -> Gate -> Registry).
"""

import os
from sagemaker.workflow.parameters import ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.sklearn.processing import SKLearnProcessor

def get_pipeline(
    pipeline_session,
    role,
    input_data_uri,
    config_uri,
    default_bucket=None
):
    """Constructs and returns the complete 12-node SageMaker Pipeline object."""
    
    # Global Parameters
    input_data = ParameterString(name="InputData", default_value=input_data_uri)
    config_data = ParameterString(name="ConfigData", default_value=config_uri)

    # 1. Data Cleaning Node
    cleaner = SKLearnProcessor(
        framework_version="1.2-1", role=role, instance_type="ml.t3.medium", instance_count=1,
        base_job_name="industrial-clean", sagemaker_session=pipeline_session
    )
    step_clean = ProcessingStep(
        name="DataCleaning",
        processor=cleaner,
        inputs=[
            ProcessingInput(source=input_data, destination="/opt/ml/processing/input"),
            ProcessingInput(source=config_data, destination="/opt/ml/processing/config")
        ],
        outputs=[
            ProcessingOutput(output_name="clean", source="/opt/ml/processing/clean")
        ],
        code="sagemaker_pipeline/src/preprocess.py",
        job_arguments=[
            "--input-path", "/opt/ml/processing/input/clean_train.parquet",
            "--output-dir", "/opt/ml/processing/clean",
            "--config-path", "/opt/ml/processing/config/config.json"
        ]
    )

    # 2. Raw Feature Check Node
    raw_checker = SKLearnProcessor(
        framework_version="1.2-1", role=role, instance_type="ml.t3.medium", instance_count=1,
        base_job_name="industrial-validate-raw", sagemaker_session=pipeline_session
    )
    step_validate_raw = ProcessingStep(
        name="RawFeatureCheck",
        processor=raw_checker,
        inputs=[
            ProcessingInput(source=step_clean.properties.ProcessingOutputConfig.Outputs["clean"].S3Output.S3Uri, destination="/opt/ml/processing/clean"),
            ProcessingInput(source=config_data, destination="/opt/ml/processing/config")
        ],
        outputs=[
            ProcessingOutput(output_name="reports", source="/opt/ml/processing/reports")
        ],
        code="sagemaker_pipeline/src/validate_raw.py",
        job_arguments=[
            "--input-dir", "/opt/ml/processing/clean",
            "--output-dir", "/opt/ml/processing/reports",
            "--config-path", "/opt/ml/processing/config/config.json"
        ]
    )

    # 3. Time-Series Split Node
    splitter = SKLearnProcessor(
        framework_version="1.2-1", role=role, instance_type="ml.t3.medium", instance_count=1,
        base_job_name="industrial-split", sagemaker_session=pipeline_session
    )
    step_split = ProcessingStep(
        name="TimeSeriesSplit",
        processor=splitter,
        inputs=[
            ProcessingInput(source=step_clean.properties.ProcessingOutputConfig.Outputs["clean"].S3Output.S3Uri, destination="/opt/ml/processing/clean"),
            ProcessingInput(source=config_data, destination="/opt/ml/processing/config")
        ],
        outputs=[
            ProcessingOutput(output_name="splits", source="/opt/ml/processing/splits")
        ],
        code="sagemaker_pipeline/src/split.py",
        job_arguments=[
            "--input-dir", "/opt/ml/processing/clean",
            "--output-dir", "/opt/ml/processing/splits",
            "--config-path", "/opt/ml/processing/config/config.json"
        ],
        depends_on=["RawFeatureCheck"]
    )

    # 4. Feature Engineering Node
    engineer = SKLearnProcessor(
        framework_version="1.2-1", role=role, instance_type="ml.t3.medium", instance_count=1,
        base_job_name="industrial-feature-engineer", sagemaker_session=pipeline_session
    )
    step_feature_engineer = ProcessingStep(
        name="FeatureEngineering",
        processor=engineer,
        inputs=[
            ProcessingInput(source=step_split.properties.ProcessingOutputConfig.Outputs["splits"].S3Output.S3Uri, destination="/opt/ml/processing/splits"),
            ProcessingInput(source=config_data, destination="/opt/ml/processing/config")
        ],
        outputs=[
            ProcessingOutput(output_name="engineered", source="/opt/ml/processing/engineered"),
            ProcessingOutput(output_name="artifacts", source="/opt/ml/processing/artifacts")
        ],
        code="sagemaker_pipeline/src/feature_engineer.py",
        job_arguments=[
            "--input-dir", "/opt/ml/processing/splits",
            "--output-dir", "/opt/ml/processing/engineered",
            "--artifacts-dir", "/opt/ml/processing/artifacts",
            "--config-path", "/opt/ml/processing/config/config.json",
            "--manifest-dir", "/opt/ml/processing/splits"
        ]
    )

    # 5. Engineered Feature Check Node
    eng_checker = SKLearnProcessor(
        framework_version="1.2-1", role=role, instance_type="ml.t3.medium", instance_count=1,
        base_job_name="industrial-validate-engineered", sagemaker_session=pipeline_session
    )
    step_validate_engineered = ProcessingStep(
        name="EngineeredFeatureCheck",
        processor=eng_checker,
        inputs=[
            ProcessingInput(source=step_feature_engineer.properties.ProcessingOutputConfig.Outputs["engineered"].S3Output.S3Uri, destination="/opt/ml/processing/engineered"),
            ProcessingInput(source=config_data, destination="/opt/ml/processing/config")
        ],
        outputs=[
            ProcessingOutput(output_name="reports", source="/opt/ml/processing/reports")
        ],
        code="sagemaker_pipeline/src/validate_engineered.py",
        job_arguments=[
            "--input-dir", "/opt/ml/processing/engineered",
            "--output-dir", "/opt/ml/processing/reports",
            "--config-path", "/opt/ml/processing/config/config.json",
            "--manifest-dir", "/opt/ml/processing/engineered"
        ]
    )

    # 6. Baseline Training Node
    trainer = SKLearnProcessor(
        framework_version="1.2-1", role=role, instance_type="ml.t3.medium", instance_count=1,
        base_job_name="industrial-train", sagemaker_session=pipeline_session
    )
    step_train = ProcessingStep(
        name="BaselineTraining",
        processor=trainer,
        inputs=[
            ProcessingInput(source=step_feature_engineer.properties.ProcessingOutputConfig.Outputs["engineered"].S3Output.S3Uri, destination="/opt/ml/processing/engineered"),
            ProcessingInput(source=config_data, destination="/opt/ml/processing/config"),
            ProcessingInput(source=step_validate_engineered.properties.ProcessingOutputConfig.Outputs["reports"].S3Output.S3Uri, destination="/opt/ml/processing/validate_engineered")
        ],
        outputs=[
            ProcessingOutput(output_name="model", source="/opt/ml/processing/model")
        ],
        code="sagemaker_pipeline/src/train.py",
        job_arguments=[
            "--input-dir", "/opt/ml/processing/engineered",
            "--output-dir", "/opt/ml/processing/model",
            "--config-path", "/opt/ml/processing/config/config.json",
            "--manifest-dir", "/opt/ml/processing/validate_engineered"
        ],
        depends_on=["EngineeredFeatureCheck"]
    )

    # 7. Model Evaluation Node
    evaluator = SKLearnProcessor(
        framework_version="1.2-1", role=role, instance_type="ml.t3.medium", instance_count=1,
        base_job_name="industrial-evaluate", sagemaker_session=pipeline_session
    )
    step_eval = ProcessingStep(
        name="ModelEvaluation",
        processor=evaluator,
        inputs=[
            ProcessingInput(source=step_train.properties.ProcessingOutputConfig.Outputs["model"].S3Output.S3Uri, destination="/opt/ml/processing/model"),
            ProcessingInput(source=step_feature_engineer.properties.ProcessingOutputConfig.Outputs["engineered"].S3Output.S3Uri, destination="/opt/ml/processing/engineered"),
            ProcessingInput(source=config_data, destination="/opt/ml/processing/config")
        ],
        outputs=[
            ProcessingOutput(output_name="evaluation", source="/opt/ml/processing/evaluation")
        ],
        code="sagemaker_pipeline/src/evaluate.py",
        job_arguments=[
            "--model-path", "/opt/ml/processing/model/model.tar.gz",
            "--test-path", "/opt/ml/processing/engineered/test_engineered.parquet",
            "--output-path", "/opt/ml/processing/evaluation",
            "--manifest-dir", "/opt/ml/processing/model"
        ]
    )

    # 8. Explainability Node
    explainer = SKLearnProcessor(
        framework_version="1.2-1", role=role, instance_type="ml.t3.medium", instance_count=1,
        base_job_name="industrial-explain", sagemaker_session=pipeline_session
    )
    step_explain = ProcessingStep(
        name="Explainability",
        processor=explainer,
        inputs=[
            ProcessingInput(source=step_train.properties.ProcessingOutputConfig.Outputs["model"].S3Output.S3Uri, destination="/opt/ml/processing/model"),
            ProcessingInput(source=step_feature_engineer.properties.ProcessingOutputConfig.Outputs["engineered"].S3Output.S3Uri, destination="/opt/ml/processing/engineered"),
            ProcessingInput(source=config_data, destination="/opt/ml/processing/config"),
            ProcessingInput(source=step_eval.properties.ProcessingOutputConfig.Outputs["evaluation"].S3Output.S3Uri, destination="/opt/ml/processing/evaluation")
        ],
        outputs=[
            ProcessingOutput(output_name="explainability", source="/opt/ml/processing/explainability")
        ],
        code="sagemaker_pipeline/src/explain.py",
        job_arguments=[
            "--model-path", "/opt/ml/processing/model/model.tar.gz",
            "--test-path", "/opt/ml/processing/engineered/test_engineered.parquet",
            "--output-dir", "/opt/ml/processing/explainability",
            "--manifest-dir", "/opt/ml/processing/evaluation"
        ]
    )

    # 9. Robustness & Stress Node
    stresser = SKLearnProcessor(
        framework_version="1.2-1", role=role, instance_type="ml.t3.medium", instance_count=1,
        base_job_name="industrial-stress", sagemaker_session=pipeline_session
    )
    step_stress = ProcessingStep(
        name="RobustnessStress",
        processor=stresser,
        inputs=[
            ProcessingInput(source=step_train.properties.ProcessingOutputConfig.Outputs["model"].S3Output.S3Uri, destination="/opt/ml/processing/model"),
            ProcessingInput(source=step_feature_engineer.properties.ProcessingOutputConfig.Outputs["engineered"].S3Output.S3Uri, destination="/opt/ml/processing/engineered"),
            ProcessingInput(source=config_data, destination="/opt/ml/processing/config"),
            ProcessingInput(source=step_explain.properties.ProcessingOutputConfig.Outputs["explainability"].S3Output.S3Uri, destination="/opt/ml/processing/explainability")
        ],
        outputs=[
            ProcessingOutput(output_name="robustness", source="/opt/ml/processing/robustness")
        ],
        code="sagemaker_pipeline/src/stress.py",
        job_arguments=[
            "--model-path", "/opt/ml/processing/model/model.tar.gz",
            "--test-path", "/opt/ml/processing/engineered/test_engineered.parquet",
            "--output-dir", "/opt/ml/processing/robustness",
            "--manifest-dir", "/opt/ml/processing/explainability"
        ],
        depends_on=["Explainability"]
    )

    # 10. Model Registry Node
    register = SKLearnProcessor(
        framework_version="1.2-1", role=role, instance_type="ml.t3.medium", instance_count=1,
        base_job_name="industrial-register", sagemaker_session=pipeline_session
    )
    step_register = ProcessingStep(
        name="ModelRegistry",
        processor=register,
        inputs=[
            ProcessingInput(source=step_train.properties.ProcessingOutputConfig.Outputs["model"].S3Output.S3Uri, destination="/opt/ml/processing/model"),
            ProcessingInput(source=step_eval.properties.ProcessingOutputConfig.Outputs["evaluation"].S3Output.S3Uri, destination="/opt/ml/processing/evaluation"),
            ProcessingInput(source=step_stress.properties.ProcessingOutputConfig.Outputs["robustness"].S3Output.S3Uri, destination="/opt/ml/processing/robustness")
        ],
        code="sagemaker_pipeline/src/register_model.py",
        job_arguments=[
            "--evaluation-path", "/opt/ml/processing/evaluation/evaluation.json",
            "--model-path", "/opt/ml/processing/model/model.tar.gz",
            "--model-package-group", "industrial-turbofan-models",
            "--min-r2", "0.55",
            "--manifest-dir", "/opt/ml/processing/robustness"
        ]
    )

    # Define Unified Pipeline
    pipeline = Pipeline(
        name="Industrial-Production-Pipeline",
        parameters=[input_data, config_data],
        steps=[
            step_clean, step_validate_raw, step_split,
            step_feature_engineer, step_validate_engineered,
            step_train, step_eval, step_explain, step_stress,
            step_register
        ],
        sagemaker_session=pipeline_session
    )
    
    return pipeline
