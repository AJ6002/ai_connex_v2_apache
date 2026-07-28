# DAG Orchestrator Component Boilerplate

This service is the **DAG & Orchestrator API**. It executes steps in the workflow, loads recipes from template folders, and manages execution state.

## Folder Directory Structure
```text
dag/
├── main.py                # FastAPI routes (exposes /api/v1/pipeline/run)
├── orchestrator.py        # Resolves DAG recipes and runs sequential stages
├── dag_mapping.json       # Copy of the 1,690 DAG ID lookup mappings
├── recipes/               # Declarative workflow recipes grouped by family
│   ├── classification/    # e.g., DAG_001.json
│   ├── regression/        # e.g., DAG_241.json
│   └── ... (10 families)
└── router/                # Router logic (routes profiles to correct DAG IDs)
```

## Recipe Scheme Format
Each recipe file (located under `recipes/<family>/DAG_<id>.json`) is structured declaratively:
```json
{
  "dag_id": "DAG_001",
  "family": "Classification",
  "prepare_recipe": {
    "impute_strategy": "mean",
    "outlier_method": "iqr",
    "encode_strategy": "one-hot",
    "scale_method": "standard",
    "text_clean": false,
    "time_align": false
  },
  "splitting_recipe": {
    "test_size": 0.2,
    "val_size": 0.1,
    "stratify": true
  },
  "training_recipe": {
    "algorithm": "Logistic Regression",
    "variant": "Standard",
    "hyperparameters": {
      "penalty": "l2",
      "C": 1.0
    },
    "validation_metrics": ["accuracy", "f1", "precision", "recall"]
  }
}
```

## Execution Flow
1. Receives recommended `dag_id` and data profile metadata from the gateway.
2. Resolves and loads the corresponding recipe configuration from the `recipes/` subdirectory.
3. Steps are simulated based on the **image's architecture**:
   - `Data Preparation (PREPARE)`
   - `Data Splitting (SPLIT)`
   - `Model Training (TRAIN)`
   - `Evaluation & Validation (EVAL)`
   - `Deployment & Monitoring (DEPLOY)`
4. Streams execution logs in real time to the dashboard terminal.
