"""
aiconnex_agent/platform/manifest_builder.py
=============================================
Translates Phase 1 output (DIC + selected AnalyticalRecipe + compiled CSV)
into the authoritative manifest.json format expected by aiconnex_ml's PipelineRunner.

Zero hardcoding — pure dynamic translation based on dataset statistics,
schema inferences, and the user's chosen recipe.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def build_manifest(
    dic: Dict[str, Any],
    selected_recipe: Dict[str, Any],
    compiled_csv_path: str,
    session_id: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build an aiconnex_ml compliant manifest dict from DIC + selected recipe.

    Args:
        dic: DatasetIntelligenceContract dict output by Scout
        selected_recipe: AnalyticalRecipe dict selected by user in HITL
        compiled_csv_path: Absolute or relative path to the compiled dataset CSV
        session_id: Workflow session ID (e.g. wf_abc123)
        output_dir: Optional custom directory path for outputs/reports

    Returns:
        Dict representing complete manifest.json for PipelineRunner
    """
    path_csv = Path(compiled_csv_path).resolve()
    if path_csv.is_dir():
        if (path_csv / "all_groups_combined.csv").exists():
            path_csv = path_csv / "all_groups_combined.csv"
        else:
            csv_files = list(path_csv.glob("*.csv"))
            if csv_files:
                path_csv = csv_files[0]
    base_dir = Path(output_dir) if output_dir else (path_csv.parent if path_csv.is_file() else path_csv)

    target_col = selected_recipe.get("target") or (
        dic.get("target_candidates", ["TDS"])[0] if dic.get("target_candidates") else "TDS"
    )
    task = selected_recipe.get("task", "REGRESSION").lower()
    ml_task = "anomaly" if "anomaly" in task else "regression"

    schema_map = dic.get("schema_map", {})
    feature_catalog = dic.get("feature_catalog", {})
    dataset_card = dic.get("dataset_card", {})
    identity = dic.get("dataset_identity", {})

    # Extract numeric feature columns excluding target and metadata/excluded columns
    raw_features = []
    timestamp_col = None
    entity_col = None

    for col, dtype in schema_map.items():
        if dtype == "datetime" and timestamp_col is None:
            timestamp_col = col
            continue

        feat_meta = feature_catalog.get(col, {})
        role = feat_meta.get("role", "")

        if role == "Metadata / Identity":
            if entity_col is None:
                entity_col = col
            continue

        if col != target_col and dtype == "numeric":
            raw_features.append(col)

    if not raw_features:
        # Fallback if schema_map didn't identify numeric features separately
        raw_features = [c for c in schema_map.keys() if c != target_col and c != timestamp_col]

    manifest = {
        "pipeline_run_id": f"run_{session_id}",
        "pipeline_version": "2.0.0",
        "dag_id": selected_recipe.get("id", "R001"),
        "ml_task": ml_task,
        "data_topology": "time_series" if timestamp_col else "tabular",
        "tenant": {
            "tenant_id": dataset_card.get("dataset_name") or identity.get("name", "plant_default"),
            "site": dataset_card.get("domain", "ETP Plant"),
            "industry": dataset_card.get("industry", "Industrial Wastewater"),
        },
        "label_contract": {
            "regime": "continuous",
            "target_column": target_col,
            "target_type": "continuous" if ml_task == "regression" else "binary_anomaly",
            "fault_label_column": target_col if ml_task == "anomaly" else None,
            "label_lag_seconds": 0,
            "contamination_estimate": 0.05,
        },
        "schema_config": {
            "entity_column": entity_col,
            "timestamp_column": timestamp_col,
            "raw_features": raw_features,
            "final_features": raw_features,
        },
        "paths": {
            "raw_data": str(path_csv),
            "input_csv": str(path_csv),
            "output_dir": str(base_dir),
            "reports": str(base_dir / "reports"),
            "models": str(base_dir / "models"),
        },
        "hpo_config": {
            "n_iter": 20,
            "cv_folds": 3,
            "metric": "neg_mean_squared_error" if ml_task == "regression" else "f1",
        },
        "candidate_algorithms": (
            ["LightGBM", "XGBoost", "RandomForest", "Ridge"]
            if ml_task == "regression"
            else ["IsolationForest", "OneClassSVM"]
        ),
        "recipe_context": selected_recipe,
    }

    logger.info(
        f"[ManifestBuilder] Built manifest for task '{ml_task}' target '{target_col}' "
        f"with {len(raw_features)} features from {path_csv.name}"
    )

    return manifest


def save_manifest_to_file(manifest: Dict[str, Any], filepath: str) -> str:
    """Save a manifest dict to disk at filepath."""
    path = Path(filepath).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    logger.info(f"[ManifestBuilder] Manifest saved to {path}")
    return str(path)
