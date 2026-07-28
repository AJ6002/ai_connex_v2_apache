# AIConnex ML Pipeline Report

**Run ID:** `reg_run_001`  
**Task:** `regression`  
**Timestamp:** `2026-07-20T07:22:15.995179`

---
## Best Model
- **Algorithm:** XGBoost
- **Model Path:** `outputs/regression/best_model.pkl`

## Evaluation Results
| Metric | Test Set |
|--------|----------|
| RMSE | 23.9925 |
| MAE  | 18.3902 |
| MAPE | 0.2661 |
| R²   | 0.8161 |
| RUL Score | 28.777 |

## Validation Gates
- **VG_1 (Data):** ✅ PASS
- **VG_2 (Model):** ✅ PASS

## Completed Steps
- [x] scope
- [x] acquire
- [x] split
- [x] feature_engineering
- [x] regression_training
- [x] deploy