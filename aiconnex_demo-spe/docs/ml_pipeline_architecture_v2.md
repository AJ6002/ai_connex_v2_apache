# ML Pipeline Architecture V2: Taxonomy-Aligned Industrial Platform

---

## Section 1: Taxonomy-Derived Architecture Rules

The taxonomy document establishes four governing principles. Every architectural decision in this document traces back to one of them.

### Rule 1: Label Availability Is the Real Fork

The split between regression and anomaly detection is not "which algorithm do we pick." It is "what kind of ground truth does the data have?"

| Label Regime | What It Means | Pipeline Consequence |
|:-------------|:-------------|:---------------------|
| **Continuous labels available** | Lab result, RUL ground truth, yield measurement exists and is timestamped. | Route to **regression track**. Supervised loss. RMSE/MAE/R² evaluation. |
| **Only a curated normal period** (no fault labels) | You know when the system was healthy, but have no labeled faults. | Route to **anomaly → semi-supervised track**. Train-on-normal. Reconstruction/density loss. |
| **Fault labels exist** (rare in industry) | You have tagged examples of known fault types. | Route to **anomaly → supervised track**. Classification loss. Precision/Recall/F1 evaluation. |
| **No labels at all** | Raw data with no ground truth of any kind. | Route to **anomaly → unsupervised track**. Statistical/distance-based methods only. |

**Design decision:** The manifest field `label_regime` is the primary routing key. Not `ml_task`. The `ml_task` field ("regression" or "anomaly") is a human-intent declaration; the `label_regime` field is the actual data-contract truth that determines which code path runs.

### Rule 2: Time-Series vs. Tabular Is an Orthogonal Axis

This is not a regression-only or AD-only concern. Both families encounter both data shapes. It cuts across everything:

| Data Shape | Split Policy | Feature Engineering | Model Class Eligibility |
|:-----------|:------------|:-------------------|:-----------------------|
| **Time-series** (sensor streams, degradation trends) | **Chronological split only.** No random shuffling. Walk-forward for HPO. | Rolling stats, lag features, spectral/FFT, sequence windowing. | LSTM, TCN, Transformer eligible. Tree models require explicit windowed features. |
| **Tabular / batch records** (per-batch summary, recipe parameters) | Standard **K-Fold or stratified K-Fold** is permissible. | Standard feature engineering. No rolling windows. | Trees, linear models, MLP. Sequence models are inappropriate. |
| **Multi-entity time-series** (fleet of engines/machines) | **GroupKFold by entity.** All cycles of Entity X go to train OR test, never split. | Per-asset vs. global normalization decision required. | Same as time-series, with generalization checks across entities. |

**Design decision:** The manifest field `data_topology` (values: `"time_series"`, `"tabular"`, `"multi_entity_time_series"`) controls the splitter, the feature engineer, and the model eligibility filter. This axis is independent of whether the task is regression or anomaly.

### Rule 3: Infrastructure Is Shared, Modeling Logic Is Not

This is the central structural rule. The taxonomy is explicit: "Attempting a single unified modeling pipeline for both families is the most common design mistake in industrial ML platforms."

**Shared across both families (one codebase):**
- Data ingestion and connector layer
- Schema validation and data-quality checks
- Time alignment / resampling utilities
- Feature engineering library (rolling stats, lag, spectral, scaling)
- Experiment tracking (run metadata, parameters, artifacts)
- Model registry and versioning
- Deployment / serving infrastructure
- Monitoring infrastructure (metric collection, dashboards, alerting transport)
- The retraining orchestration skeleton (scheduler and trigger mechanism)

**Separate per family (must not be unified):**
- Label contracts (continuous target vs. curated normal period vs. fault labels)
- Training objectives / loss functions (continuous loss vs. reconstruction/density/margin loss)
- Threshold calibration (unique to anomaly; regression has no equivalent)
- Evaluation metric computation (RMSE-family vs. Precision/Recall/Detection-Latency)
- Alerting and downstream action logic (dashboard/control-loop vs. alarm/ticketing workflow)
- Retraining trigger semantics ("performance decayed → retrain" vs. "input drifted → recalibrate threshold OR retrain normal model")

### Rule 4: Scenario Coverage Is the Deliverable

Algorithms change. The list of real-world scenarios the platform must handle does not. The architecture must be validated against this checklist, not against "does XGBoost work."

**Regression scenarios:**
- [ ] Soft sensor / virtual sensor prediction
- [ ] RUL estimation with censored data handling
- [ ] Quality prediction with sparse, lagged lab labels
- [ ] Yield prediction
- [ ] Energy/utility consumption prediction
- [ ] Cycle time / throughput prediction
- [ ] Short-horizon forecasting framed as regression
- [ ] Multi-output regression preserving cross-target correlation
- [ ] Per-asset vs. fleet-wide generalization

**Anomaly detection scenarios:**
- [ ] Point anomaly detection (spikes)
- [ ] Contextual anomaly detection (context-dependent thresholds)
- [ ] Collective / sequence anomaly detection (subtle pattern shifts)
- [ ] Drift-related anomaly / changepoint detection
- [ ] Equipment fault detection with and without labels
- [ ] Sensor spike and dropout detection (data-quality vs. process anomaly)
- [ ] Novelty detection for new operating modes
- [ ] Reconstruction-based anomaly detection (PCA, Autoencoder, LSTM-AE)
- [ ] Rule/threshold-based detection with SME-defined limits
- [ ] Multiple legitimate operating regimes explicitly modeled (not flagged as anomalies)

**Platform-level scenarios:**
- [ ] Canonical schema mapping for multi-tenant/multi-site onboarding
- [ ] Chronological (not random) train/validation splitting wherever time-series data is involved
- [ ] Separate label contracts for regression vs. AD
- [ ] Separate threshold-calibration logic isolated from the shared training harness
- [ ] Drift monitoring wired to two distinct actions (retrain vs. recalibrate) depending on family
- [ ] Explainability tooling adapted per family, not assumed identical

---

## Section 2: Gaps in the Current Architecture (V1 Audit)

### Gap 1: Single Unified Modeling Pipeline (CRITICAL)

**V1 says:** "The unified pipeline does not care which algorithm is running." The `runner.py` has a single linear step sequence for both regression and anomaly.

**Taxonomy says:** "Attempting a single unified modeling pipeline for both families is the most common design mistake in industrial ML platforms."

**Problem:** The V1 runner calls `run_baselines()` → `run_hpo()` → `evaluate_model()` in a single path. But anomaly detection has fundamentally different steps: it needs threshold calibration after training, its evaluation uses different metrics (Precision/Recall, not RMSE), and its retraining trigger means something different.

**Fix:** The runner must fork into two family-specific tracks after the shared feature engineering step. Shared infra wraps both tracks; modeling logic is separate.

---

### Gap 2: No Label Contract Separation

**V1 says:** `manifest["schema"]["target_column"]` — assumes a single continuous target exists.

**Problem:** Semi-supervised anomaly detection has no target column. It has a "normal period definition" — a time range or set of entity IDs that are known-healthy. Unsupervised AD has no labels at all. The V1 schema makes regression assumptions about what ground truth looks like.

**Fix:** Add `label_contract` section to the manifest with `regime` field (`"continuous"`, `"curated_normal"`, `"fault_labeled"`, `"unlabeled"`) and family-specific sub-fields.

---

### Gap 3: No Anomaly Supervision Routing

**V1 says:** The `ANOMALY_REGISTRY` has a `"supervised": True/False` flag. The code branches on `if spec["supervised"]: model.fit(X, y) else: model.fit(X_normal)`.

**Problem:** This is binary. The taxonomy identifies three levels: supervised, semi-supervised (train-on-normal), and unsupervised. Semi-supervised requires a curated normal dataset; unsupervised does not even require that. They have different data loading, different training, and different evaluation.

**Fix:** Add `supervision_mode` as a first-class manifest field with values `"supervised"`, `"semi_supervised"`, `"unsupervised"`. Each routes to distinct data-loading and training code.

---

### Gap 4: No Threshold Calibration Step

**V1 says:** Nothing. The anomaly pipeline has no threshold calibration step at all.

**Problem:** Every anomaly model outputs a score (reconstruction error, anomaly score, density). Converting that score into a binary "anomaly / not anomaly" decision requires a calibrated threshold — typically set at a percentile of the validation-set score distribution. This is a distinct step that regression does not have, and it is the single most important operational knob for controlling false alarm rates.

**Fix:** Add `aiconnex_ml/anomaly/threshold.py` with calibration logic. Add threshold calibration as an explicit step between training and evaluation in the anomaly track.

---

### Gap 5: No Operating-Mode Awareness

**V1 says:** Nothing about operating modes or regimes.

**Problem:** The taxonomy's #1 failure mode for anomaly detection is "multiple valid operating modes not modeled — a legitimate regime change gets flagged as an anomaly (a major source of alarm fatigue)." If a plant runs in three modes (startup, steady-state, shutdown), a model trained on steady-state data will flag every startup as anomalous.

**Fix:** Add `operating_modes` to the manifest. Add per-mode normalization in the feature engineering layer. Add mode-aware evaluation that reports metrics per operating regime.

---

### Gap 6: No Drift-Action Branching

**V1 says:** Robustness testing injects noise. There is no monitoring-time drift detection or response logic.

**Problem:** The taxonomy says drift in regression means "performance decayed → retrain." Drift in anomaly means "input distribution shifted → either recalibrate the threshold or retrain the normal-state model." These are different decisions requiring different signals. V1 treats drift as a single concept.

**Fix:** Add `aiconnex_ml/monitoring/drift.py` with separate `RegressionDriftPolicy` and `AnomalyDriftPolicy` classes. The manifest specifies `drift_action` per family.

---

### Gap 7: Evaluation Metrics Are Regression-Only

**V1 says:** `metrics.py` contains `R2, RMSE, MAE, MAPE, MaxError, confidence intervals`.

**Problem:** These are all regression metrics. None of the anomaly evaluation metrics from the taxonomy exist: Precision, Recall, F1, PR-AUC, detection latency, false alarm rate per week, point-adjust evaluation caveats.

**Fix:** Split evaluation into `aiconnex_ml/evaluation/regression_metrics.py` and `aiconnex_ml/evaluation/anomaly_metrics.py`.

---

### Gap 8: No Industrial Schema Mapping

**V1 says:** Nothing about multi-tenant, multi-site sensor naming.

**Problem:** The taxonomy says "Sensor naming, units, and tag structures vary by plant, line, and even by shift-to-shift configuration changes. A multi-tenant platform needs a canonical schema mapping layer." Without this, every new client/site is a bespoke integration project.

**Fix:** Add `aiconnex_ml/data/schema_mapping.py` and a `tenant_tag_registry` section in the manifest.

---

### Gap 9: No Split Policy Variation

**V1 says:** `splitter.py` with "Chronological, group, stratified split strategies" listed but no logic for when to use which.

**Problem:** The split policy must be driven by `data_topology`, not by manual selection. Time-series data must always use chronological splits. Tabular batch data may use K-Fold. Multi-entity time-series must use GroupKFold. This must be enforced, not suggested.

**Fix:** The splitter reads `data_topology` from the manifest and enforces the correct strategy. Random split on time-series data is a hard error, not a warning.

---

### Gap 10: Missing Scenarios

The following taxonomy scenarios have no representation in V1:
- RUL with censoring (survival regression — `lifelines` / `scikit-survival` integration)
- Quality prediction with sparse lagged labels (lag-alignment logic)
- Novelty detection (new operating mode, not a fault)
- Changepoint detection (CUSUM, Bayesian online changepoint)
- Sensor dropout vs. process anomaly (data-quality anomaly vs. real anomaly)
- Contextual anomalies (normal value in general, abnormal given current context)
- Sequence/collective anomalies (Matrix Profile, LSTM-AE)
- Per-asset vs. fleet-wide generalization testing

---

## Section 3: Revised Architecture

### Updated 7-Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     LAYER 7: OPTIONAL CLOUD SYNC                        │
│   S3 artifacts · MLflow tracking · Remote dashboard · DVC versioning    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│                   LAYER 6: CONTAINERIZED EXECUTION                      │
│   Training container (heavy, GPU) · Inference container (lightweight)   │
│   Runs on: Edge PC · On-Prem · Colab · SageMaker · K3s cluster         │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│                 LAYER 5: PORTABLE MANIFEST BACKEND                      │
│   manifest.json = single source of truth                                │
│   Contains: paths, schema, label_contract, tenant_mapping,              │
│   data_topology, operating_modes, quality_gates, drift_policy           │
│   Backend: S3, local filesystem, or SQLite                              │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│           LAYER 4: FAMILY-AWARE ORCHESTRATOR / RUNNER                   │
│   Shared steps: ingest → validate → align → features                   │
│   Then FORKS:                                                           │
│     ├── REGRESSION TRACK → train → eval → registry                     │
│     └── ANOMALY TRACK → train → threshold_calibrate → eval → registry  │
│   Orchestrator: Custom Runner / Prefect / Metaflow                      │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ (imports and calls)
┌──────────────────────────────▼──────────────────────────────────────────┐
│              LAYER 3: PYTHON MODULES / PACKAGES                         │
│   aiconnex_ml/                                                          │
│   ├── shared/         → ingestion, schema, alignment, features, utils  │
│   ├── regression/     → label_contract, training, eval, explain, drift │
│   ├── anomaly/        → label_contract, training, threshold,           │
│   │                     eval, explain, drift                           │
│   ├── registry/       → versioning, quality gates, approval (shared)   │
│   └── monitoring/     → drift detection (shared infra),                │
│                         drift action (family-specific)                  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│             LAYER 2: INDUSTRIAL SCHEMA MAPPING                          │
│   Tenant tag registry: maps plant-specific sensor names, units,         │
│   and tag IDs to canonical feature names used by the ML engine          │
│   Configured per-site. Makes new plant onboarding a config exercise.    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│                 LAYER 1: THIN NOTEBOOKS (AUTHORING)                     │
│   Used ONLY for: EDA, visualization, interactive debugging              │
│   Each cell: import function → call → display                           │
│   Zero business logic inside notebooks                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Updated Package Structure

```
aiconnex_ml/
│
├── __init__.py
├── config.py                              # Pydantic models for full manifest validation
│
├── shared/                                # ──── SHARED INFRASTRUCTURE ────
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py                      # S3/local/DB data loading
│   │   ├── contract.py                    # Schema enforcement, dtype checks, range checks
│   │   ├── schema_mapping.py              # [NEW] Tenant tag registry: plant sensor names → canonical names
│   │   ├── time_alignment.py              # [NEW] Resampling, multi-rate alignment, gap detection
│   │   └── quality_checks.py             # [NEW] Duplicate detection, null pattern analysis, continuity
│   │
│   ├── splitter/
│   │   ├── __init__.py
│   │   ├── chronological.py               # Time-series: walk-forward, expanding window
│   │   ├── group.py                       # Multi-entity: GroupKFold by asset ID
│   │   ├── stratified.py                  # Tabular/imbalanced: StratifiedKFold
│   │   └── policy.py                      # [NEW] Reads data_topology → enforces correct strategy
│   │                                      #        Raises error if random split on time-series
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   ├── rolling.py                     # Rolling mean, std, min, max, slope
│   │   ├── lag.py                         # Lag features with known-delay alignment
│   │   ├── spectral.py                    # [NEW] FFT/wavelet for vibration/acoustic data
│   │   ├── scaling.py                     # Train-only fit, transform all splits
│   │   ├── mode_normalization.py          # [NEW] Per-operating-mode normalization
│   │   └── validation.py                  # Leakage, PSI drift, collinearity, target correlation
│   │
│   ├── experiment/
│   │   ├── __init__.py
│   │   ├── tracker.py                     # [NEW] MLflow/local experiment logging
│   │   └── run_metadata.py               # [NEW] Run ID, timestamps, params, artifacts log
│   │
│   ├── explain/
│   │   ├── __init__.py
│   │   ├── shap_analysis.py               # SHAP (TreeExplainer, KernelExplainer)
│   │   ├── feature_importance.py          # Permutation importance, MDI
│   │   └── report.py                      # JSON/HTML report generation
│   │   # NOTE: Interpretation differs per family:
│   │   #   Regression: "what drives the predicted value"
│   │   #   Anomaly: "what drives the deviation from normal"
│   │
│   └── utils/
│       ├── __init__.py
│       ├── manifest.py                    # load/save manifest (S3/local/DB agnostic)
│       ├── s3.py                          # S3 upload/download helpers
│       ├── serialization.py               # Pickle, ONNX, Treelite export
│       ├── compatibility.py               # numpy type casting, version-safe wrappers
│       └── hardware.py                    # GPU/CPU detection, thread management
│
├── regression/                            # ──── REGRESSION-SPECIFIC TRACK ────
│   ├── __init__.py
│   ├── label_contract.py                  # [NEW] Validates continuous target exists, checks
│   │                                      #        timestamp alignment, censoring flags for RUL
│   ├── registry.py                        # REGRESSION_REGISTRY dict (algorithms + grids)
│   │                                      #   Includes: Linear, Ridge, Lasso, ElasticNet, PLS,
│   │                                      #   RandomForest, XGBoost, LightGBM, CatBoost,
│   │                                      #   SVR, GaussianProcess, MLP,
│   │                                      #   LSTM, TCN, Transformer (deep learning)
│   │                                      #   SurvivalRegression (Cox PH, Weibull AFT) for RUL
│   ├── baselines.py                       # Run candidate baselines, rank by primary metric
│   ├── hpo.py                             # HPO with monotonic constraints, survival losses
│   ├── losses.py                          # [NEW] MSE, MAE, Huber, asymmetric RUL scoring
│   │                                      #        (PHM08-style: late prediction penalized more)
│   ├── evaluation.py                      # [NEW] RMSE, MAE, MAPE, R², NRMSE,
│   │                                      #        per-target metrics for multi-output,
│   │                                      #        asymmetric scoring for RUL,
│   │                                      #        confidence intervals via bootstrap,
│   │                                      #        per-segment / per-asset breakdown
│   ├── plots.py                           # Predicted vs actual, residuals, distribution
│   ├── robustness.py                      # Noise injection, sensor dropout stress test
│   └── drift.py                           # [NEW] RegressionDriftPolicy:
│                                          #   Signal: performance decay on holdout
│                                          #   Action: trigger full retrain
│
├── anomaly/                               # ──── ANOMALY-SPECIFIC TRACK ────
│   ├── __init__.py
│   ├── label_contract.py                  # [NEW] Validates supervision_mode:
│   │                                      #   "supervised" → requires fault labels + class column
│   │                                      #   "semi_supervised" → requires normal_period definition
│   │                                      #   "unsupervised" → requires nothing, pure statistical
│   ├── registry.py                        # ANOMALY_REGISTRY dict (algorithms + grids)
│   │                                      #   supervision_mode=unsupervised:
│   │                                      #     IsolationForest, LOF, DBSCAN, kNN-distance,
│   │                                      #     MatrixProfile, Z-score, Mahalanobis, KDE
│   │                                      #   supervision_mode=semi_supervised:
│   │                                      #     OneClassSVM, PCA-residual, Autoencoder, VAE,
│   │                                      #     LSTM-Autoencoder, Forecasting-residual
│   │                                      #   supervision_mode=supervised:
│   │                                      #     XGBClassifier, RFClassifier, MLP
│   │                                      #   Always available:
│   │                                      #     Rule/Threshold-based (SPC: Shewhart, CUSUM, EWMA)
│   │                                      #     Changepoint detection (Bayesian online)
│   ├── data_loader.py                     # [NEW] Loads data differently per supervision_mode:
│   │                                      #   supervised: (X_train, y_train) with fault labels
│   │                                      #   semi_supervised: X_normal only (from normal_period)
│   │                                      #   unsupervised: X_all (no filtering)
│   ├── baselines.py                       # Run candidates, rank by PR-AUC or anomaly score
│   ├── hpo.py                             # HPO for contamination, nu, reconstruction error
│   ├── threshold.py                       # [NEW] ThresholdCalibrator:
│   │                                      #   - Percentile-based (e.g., 99th percentile of val scores)
│   │                                      #   - Cost-based (minimize business cost function)
│   │                                      #   - SME-defined fixed thresholds
│   │                                      #   Outputs: threshold_value, false_alarm_rate_estimate
│   ├── evaluation.py                      # [NEW] Precision, Recall, F1 (per-class and macro),
│   │                                      #        ROC-AUC, PR-AUC,
│   │                                      #        detection latency / time-to-detect,
│   │                                      #        false alarm rate per day/week,
│   │                                      #        point-adjust evaluation (with stated convention),
│   │                                      #        per-operating-mode breakdown
│   ├── plots.py                           # [NEW] Score distribution, threshold visualization,
│   │                                      #        confusion matrix, PR curve, timeline plot
│   ├── robustness.py                      # Noise injection, sensor dropout on anomaly scores
│   ├── operating_modes.py                 # [NEW] OperatingModeDetector:
│   │                                      #   - Detects mode from manifest (startup/steady/shutdown)
│   │                                      #   - Filters training data per mode
│   │                                      #   - Applies per-mode thresholds
│   │                                      #   Prevents: legitimate mode changes flagged as anomalies
│   └── drift.py                           # [NEW] AnomalyDriftPolicy:
│                                          #   Signal: input distribution shift (PSI, KS-test)
│                                          #   Actions (DISTINCT from regression):
│                                          #     1. Recalibrate threshold only (fast, cheap)
│                                          #     2. Retrain the normal-state model (expensive)
│                                          #   Decision logic:
│                                          #     If score distribution shifted but features stable
│                                          #       → recalibrate threshold
│                                          #     If feature distribution shifted
│                                          #       → retrain normal model
│
├── registry/                              # ──── SHARED MODEL REGISTRY ────
│   ├── __init__.py
│   ├── gates.py                           # Quality gate checks (family-aware: RMSE gates
│   │                                      #   for regression, false-alarm-rate gates for anomaly)
│   ├── versioning.py                      # Semantic versioning, folder management
│   └── approval.py                        # DEPLOYMENT_READY flag with audit trail
│
├── monitoring/                            # ──── SHARED MONITORING INFRA ────
│   ├── __init__.py
│   ├── drift_detector.py                  # [NEW] Shared: PSI, KS-test, feature distribution
│   │                                      #   tracking on live inference data
│   ├── drift_router.py                    # [NEW] Routes drift signal to family-specific policy:
│   │                                      #   regression → RegressionDriftPolicy
│   │                                      #   anomaly → AnomalyDriftPolicy
│   ├── inference_logger.py                # [NEW] Logs predictions, latencies, feature values
│   └── alerting.py                        # [NEW] Family-specific downstream action:
│                                          #   Regression: feed dashboard / control loop
│                                          #   Anomaly: feed alarm/ticketing with escalation rules
│
└── tests/                                 # ──── TEST SUITE ────
    ├── test_shared/
    │   ├── test_schema_mapping.py
    │   ├── test_time_alignment.py
    │   ├── test_split_policy_enforcement.py  # Assert error on random split + time-series
    │   └── test_feature_leakage.py
    ├── test_regression/
    │   ├── test_label_contract.py
    │   ├── test_baselines.py
    │   ├── test_asymmetric_scoring.py        # RUL: late > early penalty
    │   └── test_censored_rul.py              # Survival regression tests
    ├── test_anomaly/
    │   ├── test_label_contract.py
    │   ├── test_supervision_routing.py        # Verify correct data loading per mode
    │   ├── test_threshold_calibration.py
    │   ├── test_operating_modes.py            # Verify mode changes not flagged
    │   └── test_drift_action_branching.py     # Verify recalibrate vs retrain decision
    └── test_scenarios/
        ├── test_rul_with_censoring.py
        ├── test_quality_sparse_lagged.py
        ├── test_novelty_detection.py
        ├── test_changepoint.py
        ├── test_sensor_dropout_vs_process.py
        └── test_multi_operating_regime.py
```

---

## Section 4: Revised Manifest Schema

```json
{
  "pipeline_run_id": "run_20260719_plant_alpha_rul",
  "pipeline_version": "2.1.0",
  "created_at": "2026-07-19T09:45:00Z",

  "tenant": {
    "tenant_id": "plant_alpha",
    "site": "Pune-Line3",
    "tag_registry_path": "config/tenants/plant_alpha/tag_mapping.json"
  },

  "ml_task": "regression",

  "label_contract": {
    "regime": "continuous",
    "target_column": "RUL",
    "target_type": "time_to_event",
    "censoring": {
      "enabled": true,
      "censor_flag_column": "is_censored",
      "explanation": "Asset still running when data was collected (right-censored)"
    },
    "label_lag_seconds": 0,
    "label_source": "ground_truth_rul_from_run_to_failure"
  },

  "data_topology": "multi_entity_time_series",
  "entity_column": "engine_id",
  "timestamp_column": "cycle",

  "operating_modes": {
    "enabled": false,
    "mode_column": null,
    "known_modes": [],
    "normalize_per_mode": false
  },

  "schema": {
    "raw_features": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8",
                     "s9", "s10", "s11", "s12", "s13", "s14",
                     "s15", "s16", "s17", "s18", "s19", "s20", "s21"],
    "operating_setting_cols": ["os1", "os2", "os3"],
    "final_features": null,
    "dropped_features": null
  },

  "split_policy": {
    "enforced_by_topology": true,
    "strategy": "chronological_group",
    "group_column": "engine_id",
    "train_ratio": 0.7,
    "val_ratio": 0.15,
    "test_ratio": 0.15,
    "random_split_on_timeseries_is_error": true
  },

  "features_config": {
    "temporal_ordered": true,
    "time_window_sizes": [10, 20, 50],
    "lag_features": true,
    "spectral_features": false,
    "monotonic_constraints": {
      "rolling_sensor_mean_12": -1
    },
    "normalization": "per_asset"
  },

  "candidate_algorithms": ["XGBoost", "RandomForest", "LightGBM"],

  "hpo_config": {
    "method": "randomized_search",
    "n_iter": 50,
    "scoring": "neg_root_mean_squared_error",
    "cv_strategy": "predefined_split",
    "n_jobs_search": -1,
    "n_jobs_estimator": 1,
    "random_state": 42
  },

  "quality_gates": {
    "family": "regression",
    "regression_gates": {
      "max_rmse": 45.0,
      "min_r2": 0.60,
      "max_mape_pct": 25.0,
      "robustness_noise_degradation_pct": 15.0
    },
    "anomaly_gates": null
  },

  "drift_policy": {
    "family": "regression",
    "regression_drift": {
      "signal": "performance_decay_on_holdout",
      "trigger_threshold_rmse_increase_pct": 20.0,
      "action": "retrain"
    },
    "anomaly_drift": null
  },

  "deployment_target": {
    "platform": "edge_linux_arm64",
    "compilation_format": "ONNX",
    "max_model_size_mb": 50
  },

  "paths": {
    "raw_data": "data/raw/cmapss_fd001.csv",
    "processed": "data/processed/",
    "train_engineered": null,
    "val_engineered": null,
    "test_engineered": null,
    "best_model": null,
    "reports": "reports/",
    "manifest_self": "data/processed/manifest.json"
  }
}
```

### Anomaly Manifest Example (Different Label Contract)

```json
{
  "pipeline_run_id": "run_20260719_plant_beta_fault_detection",
  "ml_task": "anomaly",

  "label_contract": {
    "regime": "semi_supervised",
    "supervision_mode": "semi_supervised",
    "normal_period": {
      "start": "2026-01-01T00:00:00Z",
      "end": "2026-03-15T23:59:59Z",
      "filter_column": null,
      "filter_value": null
    },
    "contamination_estimate": 0.02,
    "fault_label_column": null,
    "anomaly_types_of_interest": ["point", "contextual", "collective"]
  },

  "operating_modes": {
    "enabled": true,
    "mode_column": "operating_regime",
    "known_modes": ["startup", "steady_state", "shutdown", "cleaning"],
    "normalize_per_mode": true
  },

  "candidate_algorithms": ["LSTM_Autoencoder", "IsolationForest", "PCA_Residual"],

  "threshold_config": {
    "method": "percentile",
    "percentile": 99.0,
    "max_false_alarm_rate_per_week": 5,
    "sme_override_threshold": null
  },

  "quality_gates": {
    "family": "anomaly",
    "regression_gates": null,
    "anomaly_gates": {
      "min_precision": 0.70,
      "min_recall": 0.85,
      "min_pr_auc": 0.60,
      "max_false_alarm_rate_per_week": 10,
      "max_detection_latency_minutes": 30
    }
  },

  "drift_policy": {
    "family": "anomaly",
    "regression_drift": null,
    "anomaly_drift": {
      "signal": "feature_distribution_shift",
      "detection_method": "psi_and_ks_test",
      "psi_threshold": 0.2,
      "action_routing": {
        "score_distribution_shifted_only": "recalibrate_threshold",
        "feature_distribution_shifted": "retrain_normal_model"
      }
    }
  }
}
```

---

## Section 5: Regression Track vs. Anomaly Track Execution Flows

### Shared Steps (Both Tracks)

```
Step 1: LOAD MANIFEST
  └─ Read manifest.json → validate with Pydantic schema

Step 2: SCHEMA MAPPING (if tenant.tag_registry_path exists)
  └─ Map plant-specific sensor tags to canonical feature names

Step 3: DATA VALIDATION
  └─ Schema conformance, per-sensor range checks, null rate,
     timestamp continuity, duplicate detection, unit consistency,
     cross-sensor correlation sanity checks

Step 4: TIME ALIGNMENT (if data_topology is time_series or multi_entity_time_series)
  └─ Resample to common clock, handle mixed sample rates,
     detect and log gaps

Step 5: SPLIT DATA
  └─ Read data_topology → enforce correct strategy:
     time_series → chronological split
     multi_entity_time_series → group chronological split
     tabular → K-Fold / stratified
     ERROR if random split on time-series data

Step 6: FEATURE ENGINEERING
  └─ Rolling, lag, spectral (shared library)
  └─ Per-operating-mode normalization (if operating_modes.enabled)
  └─ Scaling: fit on train ONLY, transform val/test

Step 7: FEATURE VALIDATION
  └─ Leakage check, collinearity check, PSI drift check
```

### Regression Track (Steps 8R–13R)

```
Step 8R: LABEL CONTRACT VALIDATION
  └─ Verify target column exists, is continuous, has correct dtype
  └─ If target_type is "time_to_event": verify censor_flag_column
  └─ Check label-to-sensor timestamp alignment

Step 9R: BASELINE TRAINING
  └─ Loop over candidate_algorithms from REGRESSION_REGISTRY
  └─ model.fit(X_train, y_train)
  └─ Rank by primary_metric (RMSE, MAE, or asymmetric RUL score)

Step 10R: HPO TUNING
  └─ RandomizedSearchCV with PredefinedSplit
  └─ Apply monotonic_constraints if specified
  └─ If target_type is "time_to_event": use survival loss, not MSE
  └─ n_jobs_estimator=1, n_jobs_search=-1

Step 11R: EVALUATION (Regression-Specific Metrics)
  └─ RMSE, MAE, MAPE, R², NRMSE
  └─ If multi-output: per-target metrics + aggregate
  └─ If RUL: asymmetric scoring (late penalty > early penalty)
  └─ Train vs. Val vs. Test gap analysis
  └─ Residual analysis and plots
  └─ Per-entity / per-segment breakdown
  └─ Confidence intervals via bootstrap

Step 12R: EXPLAINABILITY
  └─ SHAP: "what drives the predicted VALUE"
  └─ Feature importance (permutation, MDI)
  └─ Reports: JSON + plots

Step 13R: ROBUSTNESS TESTING
  └─ Gaussian noise injection at varying sigma
  └─ Sensor dropout simulation
  └─ Verify RMSE degradation < threshold
```

### Anomaly Track (Steps 8A–14A)

```
Step 8A: LABEL CONTRACT VALIDATION
  └─ Read supervision_mode from manifest:
     "supervised" → verify fault_label_column exists with class labels
     "semi_supervised" → verify normal_period time range or filter
     "unsupervised" → no validation needed (no labels expected)

Step 9A: DATA LOADING (Supervision-Mode-Specific)
  └─ supervised: load (X_train, y_train) with fault labels
  └─ semi_supervised: load X_normal only (filter to normal_period)
  └─ unsupervised: load X_all (no filtering)

Step 10A: BASELINE TRAINING
  └─ Loop over candidate_algorithms from ANOMALY_REGISTRY
  └─ Filter by supervision_mode (e.g., IsolationForest only available
     in unsupervised/semi-supervised, not supervised)
  └─ supervised: model.fit(X_train, y_train)
  └─ semi_supervised: model.fit(X_normal)
  └─ unsupervised: model.fit(X_all)
  └─ Rank by anomaly_score performance on validation set

Step 11A: THRESHOLD CALIBRATION ← NO EQUIVALENT IN REGRESSION
  └─ Compute anomaly scores on validation set
  └─ Calibrate threshold:
     percentile method → 99th percentile of val scores
     cost-based → minimize (false_alarm_cost + missed_detection_cost)
     sme_override → use fixed value from domain expert
  └─ If operating_modes.enabled:
     calibrate separate thresholds per operating mode
  └─ Output: threshold_value, estimated_false_alarm_rate

Step 12A: EVALUATION (Anomaly-Specific Metrics)
  └─ Precision, Recall, F1 (per-class and macro)
  └─ ROC-AUC, PR-AUC (PR-AUC is primary — more informative under imbalance)
  └─ Detection latency / time-to-detect
  └─ False alarm rate per day/week
  └─ Point-adjust evaluation (state which convention is used)
  └─ Per-operating-mode breakdown
  └─ Per-anomaly-type breakdown (point vs. contextual vs. collective)

Step 13A: EXPLAINABILITY
  └─ SHAP: "what drives the deviation FROM NORMAL"
  └─ Reconstruction error breakdown per sensor (for AE-based models)
  └─ Reports: JSON + plots

Step 14A: ROBUSTNESS TESTING
  └─ Noise injection → verify anomaly scores remain stable for normal data
  └─ Sensor dropout → verify dropout not falsely flagged as anomaly
  └─ Verify threshold stability under perturbation
```

### Shared Final Steps (Both Tracks)

```
Step FINAL-1: QUALITY GATE CHECK
  └─ Read quality_gates from manifest
  └─ If family == regression: check RMSE < max_rmse, R² > min_r2, etc.
  └─ If family == anomaly: check precision > min, recall > min,
     false_alarm_rate < max, detection_latency < max, etc.
  └─ Pass → status: "approved"
  └─ Fail → status: "rejected" with specific failing gate listed

Step FINAL-2: REGISTRY COMMIT
  └─ Move model to versioned folder (models/v2.1.0/)
  └─ Write DEPLOYMENT_READY flag with audit trail:
     {"status": "approved", "version": "v2.1.0",
      "approved_at": "2026-07-19T...", "gates_passed": [...]}
  └─ Save scaler, feature_cols, threshold (if anomaly), manifest alongside model
```

---

## Section 6: Missing Edge Cases and Industrial Caveats

### Edge Case 1: RUL with Right-Censoring
**Scenario:** An engine is still running when the data was collected. Its true RUL is unknown — we only know it is > T.
**Problem:** Standard regression treats this as a normal label. The model trains on `RUL = T` as if the engine failed at T. It didn't.
**Fix:** The `label_contract.censoring.enabled` flag triggers survival regression (Cox PH, Weibull AFT via `lifelines` or `scikit-survival`). The loss function properly handles right-censored observations. If censoring is enabled but the user requests a non-survival algorithm, the system warns but does not block.

### Edge Case 2: Quality Prediction with Sparse Lagged Labels
**Scenario:** Lab test results arrive 4 hours after the sensor window that produced them. Only 3 lab tests per shift.
**Problem:** Naive join aligns sensor row at time T with lab result at time T. The lab result actually corresponds to sensors at T-4h.
**Fix:** The `label_contract.label_lag_seconds` field (e.g., `14400` for 4 hours) shifts the label alignment. The feature engineer joins sensor features at `T - lag` with lab result at `T`.

### Edge Case 3: Sensor Dropout vs. Process Anomaly
**Scenario:** Sensor S7 flatlines to 0. Is this a real process event or a broken sensor?
**Problem:** Both look identical to a single-sensor anomaly model.
**Fix:** The `shared/data/quality_checks.py` module runs a "degenerate/stuck sensor" check before the anomaly model. If a sensor has zero variance for > N consecutive readings, it is flagged as a data-quality anomaly (sensor fault), not a process anomaly. This check runs before the ML model, not inside it.

### Edge Case 4: Novelty Detection (New Operating Mode)
**Scenario:** A plant starts running a new product recipe. All sensors are within physically safe ranges, but the multivariate pattern has never been seen in training data.
**Problem:** A tight anomaly model flags this as a fault. Operators ignore all future alerts (alarm fatigue).
**Fix:** The `anomaly/operating_modes.py` module maintains a registry of known modes. When a new cluster is detected that doesn't match any known mode and doesn't match any known fault signature, the system raises a "novelty" alert (distinct from "anomaly") and prompts for human classification: is this a new valid mode or a real anomaly? If confirmed as valid, the mode is added to the registry and the normal model is retrained to include it.

### Edge Case 5: Multiple Legitimate Operating Regimes
**Scenario:** A turbine has startup, steady-state, and shutdown modes. Sensor patterns differ drastically across modes.
**Problem:** A model trained on steady-state data flags every startup transition as anomalous.
**Fix:** The `operating_modes.enabled: true` flag triggers per-mode normalization in feature engineering and per-mode threshold calibration in the anomaly track. Metrics are reported per-mode, not just as a single aggregate.

### Edge Case 6: Collective / Sequence Anomalies
**Scenario:** Individual sensor readings look normal, but the pattern over a 2-hour window shows a subtle oscillation that precedes bearing failure.
**Problem:** Point-anomaly methods (Z-score, Isolation Forest) cannot detect this — each individual point is within bounds.
**Fix:** The anomaly registry includes sequence-aware methods: `LSTM_Autoencoder`, `MatrixProfile`, `TCN_Autoencoder`. The manifest field `anomaly_types_of_interest: ["collective"]` filters the algorithm search to only include methods capable of detecting collective anomalies.

### Edge Case 7: Per-Asset vs. Fleet-Wide Generalization
**Scenario:** A model trained on Engine 1-80 predicts RUL for Engine 81 (never seen in training).
**Problem:** If Engine 81 has slightly different dynamics (different maintenance history, different sensor calibration), the model may perform poorly.
**Fix:** The split policy uses GroupKFold. Evaluation reports per-entity metrics in addition to aggregate metrics. If the per-entity variance is high (e.g., RMSE ranges from 10 to 90 across entities), the system warns that the model has poor fleet-wide generalization and recommends either per-asset fine-tuning or additional entity-level features.

### Edge Case 8: Contaminated Normal Set
**Scenario:** The "normal period" used for semi-supervised anomaly training actually contains an undetected slow fault.
**Problem:** The model learns the fault pattern as "normal." Its threshold shifts upward. It misses similar faults in production.
**Fix:** Before training, `anomaly/label_contract.py` runs a statistical scan on the declared normal period: outlier fraction estimate (e.g., using Isolation Forest as a pre-filter), variance stability check, and cross-correlation stability check. If contamination estimate exceeds `contamination_estimate` from the manifest, the system warns and logs the finding.

### Edge Case 9: Forecast-Residual Bridge (Regression → Anomaly)
**Scenario:** You already have a good regression model predicting sensor S7 one step ahead. You want to use its prediction errors as an anomaly signal.
**Problem:** The taxonomy identifies this as a valid and important pattern ("bridges regression and AD") but V1 has no concept of it.
**Fix:** The anomaly registry includes `Forecasting_Residual` as an algorithm entry. This method loads an existing trained regression model, computes residuals on live data, and applies threshold calibration to those residuals. The manifest references the regression model via `forecasting_model_path`.

### Edge Case 10: Point-Adjust Evaluation Inflation
**Scenario:** An anomaly segment spans 100 timesteps. The model detects only 1 of those 100 points. Under point-adjust evaluation, the entire segment is marked as "detected."
**Problem:** Reported recall is 100% when the model actually detected 1% of the anomalous points. This inflates perceived performance.
**Fix:** `anomaly/evaluation.py` computes both raw point-level metrics AND point-adjust metrics. The report explicitly states which convention is used. The quality gates use raw metrics, not point-adjusted ones.

---

## Section 7: Concrete Edits to Apply to V1

### Edit 1: Layer Diagram — Add Schema Mapping and Fork

**Current (V1):** 6-layer diagram with single linear path.
**Replace with:** 7-layer diagram showing the schema mapping layer (Layer 2) and the fork at the orchestrator (Layer 4) into regression and anomaly tracks.

### Edit 2: Package Structure — Split into shared/ regression/ anomaly/

**Current (V1):**
```
aiconnex_ml/
├── data/
├── features/
├── training/       ← unified training for both families
├── evaluation/     ← regression metrics only
├── explain/
├── robustness/
├── registry_commit/
└── utils/
```

**Replace with:**
```
aiconnex_ml/
├── shared/          ← ingestion, schema, alignment, features, utils
├── regression/      ← label contract, training, eval (RMSE), drift (retrain)
├── anomaly/         ← label contract, training, THRESHOLD, eval (Precision/Recall), drift (recalibrate OR retrain)
├── registry/        ← shared versioning
├── monitoring/      ← shared infra, family-specific action routing
└── tests/
```

### Edit 3: runner.py — Fork After Features

**Current (V1):** Single linear step list.
**Replace with:**

```python
def run_pipeline(manifest_path: str):
    manifest = load_manifest(manifest_path)
    
    # ── SHARED STEPS ──
    manifest = apply_schema_mapping(manifest)
    manifest = validate_contract(manifest)
    manifest = align_timestamps(manifest)
    manifest = split_data(manifest)          # Enforced by data_topology
    manifest = engineer_features(manifest)
    manifest = validate_features(manifest)
    
    # ── FORK BY FAMILY ──
    if manifest["ml_task"] == "regression":
        manifest = regression_label_check(manifest)
        manifest = regression_baselines(manifest)
        manifest = regression_hpo(manifest)
        manifest = regression_evaluate(manifest)
        manifest = regression_explain(manifest)
        manifest = regression_robustness(manifest)
    
    elif manifest["ml_task"] == "anomaly":
        manifest = anomaly_label_check(manifest)
        manifest = anomaly_load_by_supervision(manifest)
        manifest = anomaly_baselines(manifest)
        manifest = anomaly_calibrate_threshold(manifest)   # ← No equivalent in regression
        manifest = anomaly_evaluate(manifest)
        manifest = anomaly_explain(manifest)
        manifest = anomaly_robustness(manifest)
    
    # ── SHARED FINAL ──
    manifest = check_quality_gates(manifest)
    manifest = commit_to_registry(manifest)
```

### Edit 4: Manifest — Add Missing Fields

**Add these top-level keys to manifest.json:**

| New Key | Type | Purpose |
|:--------|:-----|:--------|
| `tenant` | object | `tenant_id`, `site`, `tag_registry_path` for multi-site mapping |
| `label_contract` | object | `regime`, `supervision_mode`, `normal_period`, `censoring`, `label_lag_seconds` |
| `data_topology` | string | `"time_series"`, `"tabular"`, `"multi_entity_time_series"` |
| `operating_modes` | object | `enabled`, `mode_column`, `known_modes`, `normalize_per_mode` |
| `split_policy.random_split_on_timeseries_is_error` | boolean | Hard error enforcement |
| `threshold_config` | object | `method`, `percentile`, `max_false_alarm_rate_per_week`, `sme_override_threshold` |
| `quality_gates.anomaly_gates` | object | `min_precision`, `min_recall`, `min_pr_auc`, `max_false_alarm_rate_per_week`, `max_detection_latency_minutes` |
| `drift_policy` | object | Family-specific: `regression_drift.action = "retrain"` vs. `anomaly_drift.action_routing` (recalibrate vs. retrain) |

### Edit 5: Evaluation — Split Into Two Modules

**Current:** `aiconnex_ml/evaluation/metrics.py` with `R2, RMSE, MAE, MAPE, MaxError`.

**Replace with:**
- `aiconnex_ml/regression/evaluation.py` — RMSE, MAE, MAPE, R², NRMSE, asymmetric RUL scoring, multi-output per-target, bootstrap CI, per-segment breakdown
- `aiconnex_ml/anomaly/evaluation.py` — Precision, Recall, F1, ROC-AUC, PR-AUC, detection latency, false alarm rate, point-adjust (stated convention), per-mode breakdown

### Edit 6: Inference Server — Anomaly Endpoint

**Current:** Single `/predict` endpoint that returns `{"prediction": float}`.
**Add:** A separate `/detect` endpoint for anomaly models:

```python
@app.post("/detect")
async def detect(data: dict):
    features = np.array([[data[col] for col in feature_cols]])
    score = model.decision_function(features)  # or .score_samples()
    is_anomaly = float(score[0]) > threshold
    return {
        "anomaly_score": float(score[0]),
        "threshold": threshold,
        "is_anomaly": is_anomaly,
        "operating_mode": data.get("operating_mode", "unknown")
    }
```

### Edit 7: New Files to Create

| New File | Package | Purpose |
|:---------|:--------|:--------|
| `shared/data/schema_mapping.py` | shared | Tenant tag registry: plant sensor names → canonical names |
| `shared/data/time_alignment.py` | shared | Multi-rate resampling, gap detection, clock alignment |
| `shared/data/quality_checks.py` | shared | Stuck sensor detection, duplicate rows, null pattern analysis |
| `shared/splitter/policy.py` | shared | Enforces correct split strategy based on `data_topology` |
| `shared/features/spectral.py` | shared | FFT/wavelet transforms for vibration data |
| `shared/features/mode_normalization.py` | shared | Per-operating-mode normalization |
| `regression/label_contract.py` | regression | Validates continuous target, censoring, lag alignment |
| `regression/losses.py` | regression | MSE, MAE, Huber, asymmetric RUL scoring |
| `regression/drift.py` | regression | RegressionDriftPolicy (signal: performance decay; action: retrain) |
| `anomaly/label_contract.py` | anomaly | Validates supervision_mode, normal_period, fault labels |
| `anomaly/data_loader.py` | anomaly | Supervision-mode-specific data loading |
| `anomaly/threshold.py` | anomaly | ThresholdCalibrator (percentile, cost-based, SME override) |
| `anomaly/operating_modes.py` | anomaly | Mode detection, per-mode filtering and thresholds |
| `anomaly/drift.py` | anomaly | AnomalyDriftPolicy (recalibrate threshold vs. retrain normal model) |
| `monitoring/drift_detector.py` | monitoring | Shared PSI, KS-test on live inference data |
| `monitoring/drift_router.py` | monitoring | Routes drift signal to family-specific policy |
| `monitoring/inference_logger.py` | monitoring | Logs predictions, latencies, feature values |
| `monitoring/alerting.py` | monitoring | Family-specific downstream action (dashboard vs. alarm/ticket) |
