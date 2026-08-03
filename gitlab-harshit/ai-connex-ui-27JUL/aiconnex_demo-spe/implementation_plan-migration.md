# Migration Plan: Align Pipeline to `algorithm_families_complete-2.xlsx`

## Problem Statement

The entire AIConnex 9-node pipeline was built against an **older version** of the algorithm families Excel mapping. The new master file ([algorithm_families_complete-2.xlsx](file:///x:/TAS/AICONNEX/algorithm_families_complete-2.xlsx)) defines **1,993 DAG entries across 10 families**, but the pipeline code is hardcoded to an obsolete mapping where DAG ranges don't match.

### Current (WRONG) vs. New (CORRECT) Family→DAG Ranges

| Family | Family Name | OLD Code Fallback DAG | NEW Excel DAG Range | Status |
|:---|:---|:---|:---|:---|
| **F1** | Classification | `DAG_001` | `DAG_001` – `DAG_282` (282 DAGs, 15 algos) | ✅ Start correct, range unknown |
| **F2** | Regression | **`DAG_241`** ❌ | `DAG_283` – `DAG_572` (290 DAGs, 15 algos) | ❌ **DAG_241 is F1 Classification!** |
| **F3** | Anomaly Detection | `DAG_486` | `DAG_573` – `DAG_819` (247 DAGs, 15 algos) | ❌ **DAG_486 is F2 Regression!** |
| **F4** | Clustering | `DAG_696` | `DAG_820` – `DAG_1058` (239 DAGs, 16 algos) | ❌ **DAG_696 is F3 Anomaly!** |
| **F5** | Time-Series | `DAG_906` | `DAG_1059` – `DAG_1315` (257 DAGs, 13 algos) | ❌ **DAG_906 is F4 Clustering!** |
| **F6** | Digital Twin | `DAG_1131` | `DAG_1316` – `DAG_1450` (135 DAGs, 11 algos) | ❌ **DAG_1131 is F5 Time-Series!** |
| **F7** | Reinforcement Learning | `DAG_1241` | `DAG_1451` – `DAG_1571` (121 DAGs, 10 algos) | ❌ **DAG_1241 is F5 Time-Series!** |
| **F8** | Recommendation | `DAG_1341` | `DAG_1572` – `DAG_1704` (133 DAGs, 11 algos) | ❌ **DAG_1341 is F6 Digital Twin!** |
| **F9** | NLP/Text-Classification | `DAG_1451` | `DAG_1705` – `DAG_1836` (132 DAGs, 11 algos) | ❌ **DAG_1451 is F7 RL!** |
| **F10** | Computer Vision | `DAG_1561` | `DAG_1837` – `DAG_1993` (157 DAGs, 13 algos) | ❌ **DAG_1561 is F8 Recommendation!** |

> [!CAUTION]
> **Every single family except F1 has the WRONG DAG fallback ID.** A Regression task was loading a Classification recipe. An Anomaly Detection task was loading a Regression recipe. The entire routing chain was shifted by one family.

---

## Impact Analysis: 4 Nodes Require Changes

```
Node 1 (Dataset Profiler)    → detector.py: Family detection + DAG ID assignment
                                dag_mapping.json: Algorithm→DAG lookup table
Node 2 (DAG Orchestrator)    → orchestrator.py: Fallback family→DAG mapping
Node 3 (Recipe Orchestrator) → main.py: Fallback family→DAG mapping
                                recipe/training/*.json: 1,690 → 1,993 recipe JSONs
                                recipe/preparing/*.json: same
                                recipe/feature_engineering/*.json: same
                                recipe/splitting/*.json: same
Node 7 (Train API)           → main.py: Algorithm resolver (_resolve_model)
                                Currently missing: ARIMA, Prophet, SARIMA, VAR
```

---

## Proposed Changes

### Phase 1: Update DAG Fallback Mappings (3 Files)

These are the hardcoded family→DAG fallback IDs that must be corrected.

---

#### [MODIFY] [detector.py](file:///X:/TAS/AICONNEX/aic/1_dataset_profiler/detector.py)

**Lines 297–374**: Update the hardcoded algorithm selection heuristics to use correct DAG ranges from the new Excel:

| Family | Current Default Algo | New Default Algo | New Default DAG |
|:---|:---|:---|:---|
| REGRESSION | `ARIMA` (if has_date) / `XGBoost` | `LightGBM Standard` / `XGBoost Standard` | `DAG_414` / `DAG_436` |
| ANOMALY DETECTION | `Isolation Forest Standard` | `Isolation Forest Standard` | `DAG_595` |
| CLUSTERING | `K-Means Standard` | `K-Means Standard` | `DAG_820` |
| TIME-SERIES | `Prophet Standard` / `XGBoost` | `ARIMA Forecasting` / `XGBoost Time-Series` | `DAG_1073` / `DAG_1222` |

**Lines 229–238**: Update `dag_mapping.json` to contain the full 1,993-row mapping from the new Excel, replacing the old version.

---

#### [MODIFY] [orchestrator.py](file:///X:/TAS/AICONNEX/aic/2_dag/orchestrator.py)

**Lines 76–87**: Update fallback family→DAG mappings:

```python
# OLD (WRONG)                          # NEW (CORRECT)
"Classification"      → DAG_001        "Classification"      → DAG_001    # ✅ unchanged
"Regression"          → DAG_241  ❌    "Regression"          → DAG_283    # ✅ first F2 DAG
"Anomaly Detection"   → DAG_486  ❌    "Anomaly Detection"   → DAG_573    # ✅ first F3 DAG
"Clustering"          → DAG_696  ❌    "Clustering"          → DAG_820    # ✅ first F4 DAG
"Time-Series"         → DAG_906  ❌    "Time-Series"         → DAG_1059   # ✅ first F5 DAG
"Digital Twin"        → DAG_1131 ❌    "Digital Twin"        → DAG_1316   # ✅ first F6 DAG
"Reinforcement Learning" → DAG_1241 ❌ "Reinforcement Learning" → DAG_1451 # ✅ first F7 DAG
"Recommendation"      → DAG_1341 ❌    "Recommendation"      → DAG_1572   # ✅ first F8 DAG
"NLP/Text-Classification" → DAG_1451 ❌ "NLP/Text-Classification" → DAG_1705 # ✅ first F9 DAG
"Computer Vision"     → DAG_1561 ❌    "Computer Vision"     → DAG_1837   # ✅ first F10 DAG
```

---

#### [MODIFY] [main.py (Recipe Orchestrator)](file:///X:/TAS/AICONNEX/aic/3_recipe_orchestrator/main.py)

**Lines 42–63**: Same fallback mapping correction as orchestrator.py above.

---

### Phase 2: Regenerate Recipe JSON Files (4 Directories)

Currently there are **1,690 recipe JSONs** per directory. The new Excel defines **1,993 DAGs**. We need to:

1. **Generate 303 new recipe JSONs** (DAG_1691 through DAG_1993) across all 4 directories.
2. **Validate existing 1,690 JSONs** — ensure each DAG's `algorithm` and `variant` fields match the new Excel mapping.

#### [NEW] [generate_recipes.py](file:///X:/TAS/AICONNEX/aic/3_recipe_orchestrator/generate_recipes.py)

Script to read `algorithm_families_complete-2.xlsx` and auto-generate all 1,993 recipe JSONs per directory:

- `recipe/training/{DAG_ID}.json` → `{"algorithm": "...", "variant": "...", "validation_metrics": [...], "hyperparameters": {...}}`
- `recipe/preparing/{DAG_ID}.json` → Standard impute/scale/encode defaults per family
- `recipe/feature_engineering/{DAG_ID}.json` → Family-appropriate feature engineering defaults
- `recipe/splitting/{DAG_ID}.json` → Family-appropriate split strategy

---

### Phase 3: Update `dag_mapping.json` (Auto-Generated)

#### [MODIFY] [dag_mapping.json](file:///X:/TAS/AICONNEX/aic/1_dataset_profiler/dag_mapping.json)

Replace the entire file with a JSON representation of the new Excel mapping:

```json
{
  "CLASSIFICATION": [
    {"dag_id": "DAG_001", "algorithm": "AdaBoost", "variant": "Standard"},
    {"dag_id": "DAG_002", "algorithm": "AdaBoost", "variant": "SAMME"},
    ...
    {"dag_id": "DAG_282", "algorithm": "Voting Classifier", "variant": "Adversarial"}
  ],
  "REGRESSION": [
    {"dag_id": "DAG_283", "algorithm": "ARIMA", "variant": "Standard"},
    ...
    {"dag_id": "DAG_572", "algorithm": "Voting Regressor", "variant": "Adversarial"}
  ],
  ...
}
```

#### [NEW] [generate_dag_mapping.py](file:///X:/TAS/AICONNEX/aic/1_dataset_profiler/generate_dag_mapping.py)

Script to auto-generate `dag_mapping.json` from the Excel so it stays in sync.

---

### Phase 4: Extend Train API Model Resolver

#### [MODIFY] [main.py (Train API)](file:///X:/TAS/AICONNEX/aic/7_train/main.py)

**Lines 249–312** (`_resolve_model`): Currently falls back to `LinearRegression()` for ARIMA/Prophet/Time-Series. Must add:

| Algorithm | Implementation | Priority |
|:---|:---|:---|
| `Gradient Boosting` (Regression) | `GradientBoostingRegressor` from sklearn | 🔴 High |
| `ARIMA` / `SARIMA` / `SARIMAX` | `pmdarima.auto_arima` or `statsmodels.SARIMAX` | 🟡 Medium |
| `Prophet` | `prophet.Prophet` | 🟡 Medium |
| `VAR` (Vector Autoregression) | `statsmodels.VAR` | 🟡 Medium |
| `AdaBoost` (Regression) | `AdaBoostRegressor` from sklearn | 🟢 Low |
| `Elastic Net` | `ElasticNet` from sklearn | 🟢 Low |
| `SVR` (Support Vector Regression) | `SVR` from sklearn | 🟢 Low |
| `K-Nearest Neighbors` (Regression) | `KNeighborsRegressor` from sklearn | 🟢 Low |
| `Decision Tree` (Regression) | `DecisionTreeRegressor` from sklearn | 🟢 Low |

---

## Verification Plan

### Test 1: Trend Data Forecast (Regression → LightGBM)
```bash
python aic/run_pipeline.py --dataset workspace_data/trend_clean.csv --target PNB950657_TT02 --output workspace_data/trend_v2_run
```
- Verify DAG routes to `DAG_414` (F2 Regression / LightGBM Standard) instead of `DAG_241`
- Expect $R^2 > 0.80$ (vs. current 0.59 with Linear Regression)

### Test 2: C-MAPSS RUL (Regression → XGBoost)
```bash
python aic/run_pipeline.py --dataset workspace_data/cmapss_compiled/all_groups_combined.csv --target RUL --output workspace_data/cmapss_v2_run
```
- Verify DAG routes to F2 Regression range (DAG_283–572)

### Test 3: FEMTO Bearing RUL (Regression → Gradient Boosting)
```bash
python aic/run_pipeline.py --dataset workspace_data/femto_compiled/group_learning_set_merged.csv --output workspace_data/femto_v2_run
```
- Verify improved R² over current 0.3175

### Test 4: Insurance (Classification → XGBoost)
```bash
python aic/run_pipeline.py --dataset testing_ds/insurance.csv --target charges --output workspace_data/insurance_v2_run
```
- Verify classification tasks still route correctly within F1 range (DAG_001–282)

---

## Open Questions

> [!IMPORTANT]
> **Q1: Smart Algorithm Selection Heuristic**
> The `detector.py` currently uses simple if/else rules (row count, outlier %, correlation) to pick algorithms within a family. Should we:
> - **A)** Keep the heuristic but update it to pick from the correct DAG range?
> - **B)** Add a lightweight AutoML competition (train 3 candidate algorithms, pick the best R² in 30 seconds)?

> [!IMPORTANT]
> **Q2: Recipe JSON Regeneration Strategy**
> - **A)** Regenerate ALL 1,993 × 4 = 7,972 recipe JSONs from the Excel in one batch?
> - **B)** Only generate the missing 303 new DAGs (1691–1993) and validate existing ones?

> [!IMPORTANT]
> **Q3: ARIMA / Prophet / SARIMAX Implementation**
> The Train API currently falls back to `LinearRegression()` for these algorithms. Should we:
> - **A)** Install `pmdarima` + `prophet` and implement proper time-series models?
> - **B)** Keep using XGBoost/LightGBM with lag features as a proxy (already works well for C-MAPSS/FEMTO)?
