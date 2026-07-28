# Dataset Profiler Component Boilerplate

This service is the **Dataset Profiler API**. It analyzes tabular datasets, outputs summary statistics, and determines the recommended DAG workflow run ID from the database of 1,690 DAG configurations.

## Folder Directory Structure
```text
dataset_profiler/
├── main.py                # FastAPI routes (exposes /api/v1/profile)
├── profiler.py            # Extracts column-wise statistical summaries
├── detector.py            # Heuristics for family matching and DAG ID recommendation
├── dag_mapping.json       # Database of all 1,690 unique DAG IDs and configurations
└── requirements.txt       # Dependencies (pandas, openpyxl, fastapi, uvicorn)
```

## 1690 DAG ID Decision Mapping Logic
The decision lookup is managed inside [detector.py](file:///c:/Users/admin.DESKTOP-17T37DJ/Desktop/aic/dataset_profiler/detector.py):
1. **Target Identification**: Searches for label/outcome keywords or uses manual target overrides.
2. **Task Resolution**: Checks the target column dtype and cardinality:
   - Categorical / low cardinality $\rightarrow$ `Classification` (Binary/Multiclass).
   - Numeric / high cardinality $\rightarrow$ `Regression`.
   - Date column present $\rightarrow$ `Time-Series`.
   - No target $\rightarrow$ runs suitability checks for `Anomaly Detection` or `Clustering`.
3. **DAG ID Selection**: Queries `dag_mapping.json` for the chosen family to find the best algorithm and variant matching the metrics:
   - Small datasets $\rightarrow$ selects regularized or SVM variants.
   - Large datasets $\rightarrow$ selects LightGBM/SGD variants.
   - Multicollinearity present $\rightarrow$ selects Ridge/Lasso regularization variants.
   - Text features present $\rightarrow$ selects NLP/text classifiers (e.g. Naïve Bayes or BERT).
