# Engineering & Architectural Log: SageMaker ML Pipeline
**Project:** NASA C-MAPSS Turbofan Engine RUL Prediction Pipeline
**Date:** July 15, 2026
**Author:** Antigravity (Google DeepMind Team)

---

## 1. Executive Summary & Context
The objective of this project was to establish a production-grade, automated Machine Learning pipeline for the **NASA C-MAPSS (Turbofan Engine Degradation) dataset** to predict the Remaining Useful Life (RUL) of engines.

The target lifecycle is:
$$\text{S3 Raw Data} \longrightarrow \text{Preprocessing (Glue/Spark)} \longrightarrow \text{Model Training (Scikit-Learn)} \longrightarrow \text{Model Evaluation} \longrightarrow \text{Model Registry}$$

All scripts have been successfully authored, validated locally via Docker, tested on SageMaker Notebook instances, and orchestrated as serverless AWS Glue nodes in an **Apache Airflow (MWAA)** workflow inside SageMaker Unified Studio.

---

## 2. End-to-End Pipeline Architecture

```
                 [ S3 Raw Data: clean_train.parquet ]
                                │
                                ▼
    Step 1: Preprocessing (Glue Spark Job: cmapss-preprocess-v2)
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
           [ train.csv ]                  [ val.csv ]
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
    Step 2: Model Training (Jupyter Operator / Glue / Local Mode)
                                │
                                ▼
           [ model.tar.gz (Double-nested tarball) ]
                                │
                                ▼
    Step 3: Evaluation (Glue Spark Job: cmapss-evaluation)
                                │
                                ▼
                     [ evaluation.json ]
                                │
                                ▼
    Step 4: Quality Gate & Registry (Glue Job: cmapss-register-model-job)
                                │
                     (Check R² Score > 0.55)
                                │
               ┌────────────────┴────────────────┐
               ▼ (Pass)                          ▼ (Fail)
     [ Model Registered! ]             [ Pipeline Aborted ]
```

### Component Details
1.  **Preprocessing (`preprocess.py`):** Consumes `clean_train.parquet`, performs standard scaling, selects 101 features, and splits data into `train.csv` (127,929 rows) and `val.csv` (32,430 rows).
2.  **Training (`train.py`):** Fits a `RandomForestRegressor` (100 estimators) on training features and saves the model inside a `model.tar.gz` archive.
3.  **Evaluation (`evaluate.py`):** Evaluates `model.tar.gz` predictions on the validation set, generating regression metrics (RMSE, MAE, R²).
4.  **Registration (`register_model.py`):** Reads the evaluation metrics. If $R^2 > 0.55$, it registers the model package under `cmapss-turbofan-models` in the SageMaker Model Registry; otherwise, it throws a non-zero exit code to abort the Airflow DAG.

---

## 3. Decision Pathways & Blocker Resolution Log

### 🚨 Blocker 1: SageMaker Training Quota Limit (`ResourceLimitExceeded`)
*   **Context:** When attempting to launch a cloud training job on `ml.m5.large` or `ml.m4.xlarge`, the API returned an instance count limit of `0`.
*   **Thought Process:** Newer AWS accounts restrict SageMaker training instances to 0 by default to prevent abuse. 
*   **Decision Pathway:**
    1.  *Immediate Workaround:* Shifted to **SageMaker Local Mode** using the local Docker daemon. This streamed data from S3, executed training locally, and pushed the results back to S3.
    2.  *Notebook Sandbox:* Provisioned an `ml.t3.medium` SageMaker Notebook Instance. Trained the model in a Jupyter Notebook cell using `conda_pytorch` to bypass quotas.
    3.  *Production Ticket:* Submitted an AWS Support ticket to increase `ml.m5.large` training instances to `2` (Approved & Active).
    4.  *Workaround Bypass:* Discussed running the training script as a **Serverless AWS Glue Job** or an **AWS ECS Fargate Task** to bypass SageMaker instance restrictions entirely in future environments.

### 🐛 Blocker 2: Spark/Glue 5.0 Initialization Mismatch
*   **Context:** Running the preprocessor as a Glue job threw a Java method signature mismatch on `job.init()`.
*   **Thought Process:** Glue 5.0 runtime uses a strict signature expecting the Job Name string and the arguments dictionary.
*   **Resolution:** Modified `preprocess.py` to use `getResolvedOptions(sys.argv, ['JOB_NAME'])` and passed the resolved options dictionary directly into `job.init()`.

### 📦 Blocker 3: Double-Nested Tarball Extraction Failure
*   **Context:** The evaluation job threw `EOFError` or failed to load the model pickle.
*   **Thought Process:** SageMaker Local Mode automatically wraps the output directory's `model.tar.gz` into *another* `model.tar.gz`. The evaluation script was only unpacking one layer, finding another tarball instead of the raw `model.pkl`.
*   **Resolution:** Rewrote the model loading block in `evaluate.py` to recursively extract `.tar.gz` files up to a depth of 5 layers until the target `model.pkl` is located.

### ⚙️ Blocker 4: Scikit-Learn Version Mismatch (`missing_go_to_left`)
*   **Context:** The Glue evaluation job threw a dtype size mismatch error: `missing_go_to_left field in tree node structure not recognized`.
*   **Thought Process:** The model was trained inside the Docker container with `scikit-learn 1.2.1` but the Glue job was loading it with `1.3.2` or `1.5.0` (which introduced new split parameters).
*   **Resolution:** Downgraded/aligned all scikit-learn instances to `1.2.1`. Added `--additional-python-modules: scikit-learn==1.2.1` to the Glue job parameters.

---

## 4. Cheat Sheet of Key Commands

### S3 & Data Management
```bash
# Verify preprocessed S3 files
aws s3 ls s3://aiconnex-cleaned/cmapss/v1/preprocessed/ --recursive

# Upload python scripts to Glue DAG directory
aws s3 cp sagemaker_pipeline/src/preprocess.py s3://aiconnex-cleaned/cmapss/v1/preprocessed/code/preprocess.py
aws s3 cp sagemaker_pipeline/src/evaluate.py s3://aiconnex-cleaned/cmapss/v1/preprocessed/code/evaluate.py
aws s3 cp sagemaker_pipeline/src/register_model.py s3://aiconnex-cleaned/cmapss/v1/preprocessed/code/register_model.py
```

### Local Validation & Docker Verification
```bash
# Verify scikit-learn version in the SageMaker training image
docker run --rm 720646828776.dkr.ecr.ap-south-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3 python3 -c "import sklearn; print(sklearn.__version__)"

# Check current SageMaker training quotas via CLI
aws service-quotas list-service-quotas --service-code sagemaker --query "Quotas[?QuotaName=='ml.m5.large for training job usage'].{QuotaName:QuotaName,Value:Value}" --output json
```

### Jupyter Environment Setup (Interactive Check)
```python
# Force-install compatible numpy and sklearn versions to resolve binary clashes
!pip install "numpy<2.0.0" scikit-learn==1.2.1 --force-reinstall
# (Must restart Jupyter kernel after running this cell)
```

---

## 5. Production Airflow Orchestration DAG (YAML)

This YAML configuration coordinates your entire pipeline inside **SageMaker Unified Studio Workflows**:

```yaml
# {"Process":{"x":150,"y":200},"Evaluation":{"x":400,"y":200},"Register-Model-task":{"x":650,"y":200}}
demo-workflow:
  dag_id: demo-workflow
  is_paused_upon_creation: false
  tasks:
    Process:
      operator: airflow.providers.amazon.aws.operators.glue.GlueJobOperator
      job_name: cmapss-preprocess-v2

    Evaluation:
      dependencies:
        - Process
      operator: airflow.providers.amazon.aws.operators.glue.GlueJobOperator
      job_name: cmapss-evaluation

    Register-Model-task:
      dependencies:
        - Evaluation
      operator: airflow.providers.amazon.aws.operators.glue.GlueJobOperator
      job_name: cmapss-register-model-job
```

---

## 6. Future Constraints & Structural Guidelines
*   **Staging vs. Production Quotas:** When transferring this workflow to a new AWS region or account, check that `ml.m5.large` and `ml.t3.medium` quotas are provisioned beforehand.
*   **Version Pinning:** Always pin `scikit-learn==1.2.1` in all pipeline training/execution scripts to prevent serialization errors.
*   **Spot Instances:** Do not enable Managed Spot Training unless `spot training job usage` quotas are explicitly requested and approved.
*   **Serverless Scaling:** For heavy deep-learning workloads in the future, prioritize shifting tasks into **AWS ECS Fargate** containers triggered by Airflow `EcsRunTaskOperator`.
