"""
config.py — Pydantic manifest schema validation models
=======================================================
Validates the full manifest.json structure before any pipeline step runs.
Every new field added to the manifest MUST have a corresponding model here.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


# ──────────────────────────────────────────────────────────────────────────────
# Tenant
# ──────────────────────────────────────────────────────────────────────────────

class TenantConfig(BaseModel):
    tenant_id: str
    site: Optional[str] = None
    tag_registry_path: Optional[str] = None  # path to JSON tag mapping file


# ──────────────────────────────────────────────────────────────────────────────
# Label Contract
# ──────────────────────────────────────────────────────────────────────────────

class CensoringConfig(BaseModel):
    enabled: bool = False
    censor_flag_column: Optional[str] = None
    explanation: Optional[str] = None


class LabelContract(BaseModel):
    regime: Literal["continuous", "curated_normal", "fault_labeled", "unlabeled"]
    supervision_mode: Optional[Literal["supervised", "semi_supervised", "unsupervised"]] = None
    target_column: Optional[str] = None
    target_type: Optional[Literal["scalar", "multi_output", "time_to_event", "horizon_forecast"]] = None
    censoring: Optional[CensoringConfig] = CensoringConfig()
    label_lag_seconds: int = 0
    label_source: Optional[str] = None
    normal_period: Optional[Dict[str, Any]] = None  # {"start": ..., "end": ...} or filter dict
    contamination_estimate: float = 0.05
    fault_label_column: Optional[str] = None
    anomaly_types_of_interest: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_label_contract(self) -> "LabelContract":
        if self.regime == "continuous" and self.target_column is None:
            raise ValueError("regime='continuous' requires target_column to be set.")
        if self.regime == "curated_normal" and self.normal_period is None:
            raise ValueError("regime='curated_normal' requires normal_period to be defined.")
        if self.regime == "fault_labeled" and self.fault_label_column is None:
            raise ValueError("regime='fault_labeled' requires fault_label_column to be set.")
        return self


# ──────────────────────────────────────────────────────────────────────────────
# Operating Modes
# ──────────────────────────────────────────────────────────────────────────────

class OperatingModesConfig(BaseModel):
    enabled: bool = False
    mode_column: Optional[str] = None
    known_modes: List[str] = []
    normalize_per_mode: bool = False


# ──────────────────────────────────────────────────────────────────────────────
# Schema
# ──────────────────────────────────────────────────────────────────────────────

class SchemaConfig(BaseModel):
    raw_features: List[str] = []
    operating_setting_cols: Optional[List[str]] = None
    final_features: Optional[List[str]] = None
    dropped_features: Optional[List[str]] = None
    entity_column: Optional[str] = None
    timestamp_column: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Split Policy
# ──────────────────────────────────────────────────────────────────────────────

class SplitPolicy(BaseModel):
    enforced_by_topology: bool = True
    strategy: Optional[str] = None  # auto-derived if enforced_by_topology=True
    group_column: Optional[str] = None
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    random_state: int = 42
    random_split_on_timeseries_is_error: bool = True


# ──────────────────────────────────────────────────────────────────────────────
# Features Config
# ──────────────────────────────────────────────────────────────────────────────

class FeaturesConfig(BaseModel):
    temporal_ordered: bool = False
    time_window_sizes: List[int] = [10, 20, 50]
    lag_features: bool = True
    spectral_features: bool = False
    monotonic_constraints: Optional[Dict[str, int]] = None
    normalization: Literal["global", "per_asset", "per_mode"] = "global"


# ──────────────────────────────────────────────────────────────────────────────
# HPO Config
# ──────────────────────────────────────────────────────────────────────────────

class HPOConfig(BaseModel):
    method: Literal["randomized_search", "grid_search", "bayesian"] = "randomized_search"
    n_iter: int = 30
    scoring: str = "neg_root_mean_squared_error"
    cv_strategy: Literal["predefined_split", "kfold", "walk_forward"] = "predefined_split"
    n_jobs_search: int = -1
    n_jobs_estimator: int = 1
    random_state: int = 42


# ──────────────────────────────────────────────────────────────────────────────
# Threshold Config (Anomaly only)
# ──────────────────────────────────────────────────────────────────────────────

class ThresholdConfig(BaseModel):
    method: Literal["percentile", "cost_based", "sme_override"] = "percentile"
    percentile: float = 99.0
    max_false_alarm_rate_per_week: Optional[int] = None
    sme_override_threshold: Optional[float] = None


# ──────────────────────────────────────────────────────────────────────────────
# Quality Gates
# ──────────────────────────────────────────────────────────────────────────────

class RegressionGates(BaseModel):
    max_rmse: Optional[float] = None
    min_r2: Optional[float] = None
    max_mape_pct: Optional[float] = None
    robustness_noise_degradation_pct: float = 15.0


class AnomalyGates(BaseModel):
    min_precision: Optional[float] = None
    min_recall: Optional[float] = None
    min_pr_auc: Optional[float] = None
    max_false_alarm_rate_per_week: Optional[int] = None
    max_detection_latency_minutes: Optional[int] = None


class QualityGates(BaseModel):
    family: Literal["regression", "anomaly", "classification", "clustering"]
    regression_gates: Optional[RegressionGates] = None
    anomaly_gates: Optional[AnomalyGates] = None


# ──────────────────────────────────────────────────────────────────────────────
# Drift Policy
# ──────────────────────────────────────────────────────────────────────────────

class RegressionDriftConfig(BaseModel):
    signal: str = "performance_decay_on_holdout"
    trigger_threshold_rmse_increase_pct: float = 20.0
    action: Literal["retrain"] = "retrain"


class AnomalyDriftActionRouting(BaseModel):
    score_distribution_shifted_only: Literal["recalibrate_threshold"] = "recalibrate_threshold"
    feature_distribution_shifted: Literal["retrain_normal_model"] = "retrain_normal_model"


class AnomalyDriftConfig(BaseModel):
    signal: str = "feature_distribution_shift"
    detection_method: Literal["psi_and_ks_test", "psi_only", "ks_only"] = "psi_and_ks_test"
    psi_threshold: float = 0.2
    action_routing: AnomalyDriftActionRouting = AnomalyDriftActionRouting()


class DriftPolicy(BaseModel):
    family: Literal["regression", "anomaly"]
    regression_drift: Optional[RegressionDriftConfig] = None
    anomaly_drift: Optional[AnomalyDriftConfig] = None


# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

class PathsConfig(BaseModel):
    raw_data: Optional[str] = None
    processed: Optional[str] = None
    train_engineered: Optional[str] = None
    val_engineered: Optional[str] = None
    test_engineered: Optional[str] = None
    best_model: Optional[str] = None
    scaler: Optional[str] = None
    threshold: Optional[str] = None  # Anomaly: saved calibrated threshold
    reports: Optional[str] = None
    manifest_self: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Deployment Target
# ──────────────────────────────────────────────────────────────────────────────

class DeploymentTarget(BaseModel):
    platform: Literal["edge_linux_arm64", "edge_linux_x86", "cloud_sagemaker", "local"] = "local"
    compilation_format: Optional[Literal["ONNX", "Treelite", "pickle"]] = "pickle"
    max_model_size_mb: Optional[int] = None


# ──────────────────────────────────────────────────────────────────────────────
# Root Manifest
# ──────────────────────────────────────────────────────────────────────────────

class Manifest(BaseModel):
    pipeline_run_id: str
    pipeline_version: str = "2.0.0"
    dag_id: Optional[str] = None
    created_at: Optional[str] = None

    tenant: Optional[TenantConfig] = None
    ml_task: Literal["regression", "anomaly", "classification", "clustering"]
    label_contract: LabelContract
    data_topology: Literal["time_series", "tabular", "multi_entity_time_series"] = "tabular"

    schema_config: SchemaConfig = SchemaConfig()
    operating_modes: OperatingModesConfig = OperatingModesConfig()
    split_policy: SplitPolicy = SplitPolicy()
    features_config: FeaturesConfig = FeaturesConfig()
    candidate_algorithms: List[str] = []
    hpo_config: HPOConfig = HPOConfig()
    threshold_config: Optional[ThresholdConfig] = None
    quality_gates: Optional[QualityGates] = None
    drift_policy: Optional[DriftPolicy] = None
    deployment_target: DeploymentTarget = DeploymentTarget()
    paths: PathsConfig = PathsConfig()

    # Runtime state fields (written by pipeline steps)
    status: str = "pending"
    completed_steps: List[str] = []
    registry: Dict[str, Any] = {}
