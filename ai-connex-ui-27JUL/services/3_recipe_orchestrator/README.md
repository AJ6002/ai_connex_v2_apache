# Recipe Orchestrator Component Boilerplate

This service is the **Recipe Orchestrator API**. It compiles separate preparing, splitting, and training recipes matching a given DAG ID into a runtime configuration.

## Folder Directory Structure
```text
recipe_orchestrator/
├── main.py                # FastAPI routes (exposes /api/v1/orchestrate)
├── recipe/                # Isolated recipe folders
│   ├── preparing/         # JSON recipe for preprocessing (impute, scale)
│   ├── splitting/         # JSON recipe for partitioning ratios
│   └── training/          # JSON recipe for model fitting and metrics
├── meta/                  # Directory containing compiled runtime recipes
│   └── meta3.json         # Compiled unified configuration for the current run
└── requirements.txt       # Dependencies (fastapi, uvicorn)
```

## Compilation Logic
When a POST request is sent to `/api/v1/orchestrate`:
1. It reads `meta1.json` (Dataset profile summary) and `meta2.json` (DAG recommendation details).
2. Resolves the recommended `dag_id` (e.g. `DAG_061`).
3. Loads the 3 component-level recipe files:
   - `recipe/preparing/{dag_id}.json`
   - `recipe/splitting/{dag_id}.json`
   - `recipe/training/{dag_id}.json`
   *(If a specific recipe does not exist, it falls back to the default recipe matching that algorithm family, such as classification $\rightarrow$ `DAG_001.json`).*
4. Merges the 3 recipes with structural metadata and saves the compiled output to `meta/meta3.json`, which acts as the unified blueprint for downstream microservices.
