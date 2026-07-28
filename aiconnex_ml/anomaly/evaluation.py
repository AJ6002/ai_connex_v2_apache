"""
evaluation.py — Anomaly detection evaluation metrics
=====================================================
Computes Precision, Recall, F1, ROC-AUC, PR-AUC, detection latency,
false alarm rate per week, and per-operating-mode breakdowns.

PR-AUC is the primary metric (more informative than ROC-AUC under imbalance).
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

try:
    from sklearn.metrics import (
        precision_score, recall_score, f1_score,
        roc_auc_score, average_precision_score,
        confusion_matrix,
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def compute_anomaly_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: np.ndarray,
    label: str = "overall",
) -> Dict[str, Any]:
    """
    Compute classification and ranking metrics for anomaly detection.

    Args:
        y_true:  Binary ground truth (1=anomaly, 0=normal).
        y_pred:  Binary predictions after threshold application.
        scores:  Raw anomaly scores (for ROC-AUC and PR-AUC).
        label:   Label for logging (e.g., mode name).

    Returns:
        Metrics dict.
    """
    y_true = np.array(y_true).flatten()
    y_pred = np.array(y_pred).flatten()
    scores = np.array(scores).flatten()

    n_anomaly = int(y_true.sum())
    n_total = len(y_true)

    metrics: Dict[str, Any] = {
        "label": label,
        "n_total": n_total,
        "n_true_anomalies": n_anomaly,
        "prevalence": round(n_anomaly / max(n_total, 1), 4),
    }

    if n_anomaly == 0:
        print(f"[AnomalyEval] No positive samples in '{label}' — skipping classification metrics.")
        metrics["note"] = "No anomaly labels available — unsupervised evaluation only."
        metrics["mean_score_normal"] = round(float(scores[y_true == 0].mean()), 4) if (y_true == 0).any() else None
        return metrics

    # Classification metrics
    zero_div = 0
    metrics["precision"] = round(float(precision_score(y_true, y_pred, zero_division=zero_div)), 4)
    metrics["recall"] = round(float(recall_score(y_true, y_pred, zero_division=zero_div)), 4)
    metrics["f1"] = round(float(f1_score(y_true, y_pred, zero_division=zero_div)), 4)

    # Ranking metrics
    try:
        metrics["pr_auc"] = round(float(average_precision_score(y_true, scores)), 4)
        metrics["roc_auc"] = round(float(roc_auc_score(y_true, scores)), 4)
    except Exception:
        metrics["pr_auc"] = None
        metrics["roc_auc"] = None

    # False alarm rate (per day estimate — assumes hourly inference by default)
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    n_normal = int((y_true == 0).sum())
    far = fp / max(n_normal, 1)
    metrics["false_alarm_rate"] = round(far, 4)
    metrics["false_alarm_rate_per_week_estimate"] = round(far * 7 * 24, 1)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    metrics["confusion_matrix"] = cm.tolist()

    print(f"[AnomalyEval] {label}: Precision={metrics['precision']} "
          f"Recall={metrics['recall']} F1={metrics['f1']} "
          f"PR-AUC={metrics['pr_auc']} FAR/week≈{metrics['false_alarm_rate_per_week_estimate']}")

    return metrics


def compute_detection_latency(
    y_true_series: pd.Series,
    y_pred_series: pd.Series,
    timestamps: Optional[pd.Series] = None,
) -> Dict[str, Any]:
    """
    Compute average detection latency: time from first anomaly to first correct detection.

    Returns:
        {"mean_latency_steps": float, "mean_latency_minutes": float (if timestamps provided)}
    """
    latencies = []
    in_anomaly = False
    anomaly_start = None

    for i, (true, pred) in enumerate(zip(y_true_series, y_pred_series)):
        if true == 1 and not in_anomaly:
            in_anomaly = True
            anomaly_start = i
        if in_anomaly and pred == 1:
            latencies.append(i - anomaly_start)
            in_anomaly = False
            anomaly_start = None
        if true == 0:
            in_anomaly = False
            anomaly_start = None

    if not latencies:
        return {"mean_latency_steps": None, "note": "No detected anomaly segments."}

    mean_steps = float(np.mean(latencies))
    result = {"mean_latency_steps": round(mean_steps, 2)}

    if timestamps is not None:
        try:
            ts = pd.to_datetime(timestamps)
            step_duration = ts.diff().dropna().median()
            mean_latency_min = mean_steps * step_duration.total_seconds() / 60
            result["mean_latency_minutes"] = round(mean_latency_min, 2)
        except Exception:
            pass

    return result


def per_entity_anomaly_metrics(
    df_test: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: np.ndarray,
    entity_col: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Compute classification and false alarm metrics per entity (e.g., per machine/sensor).
    """
    results = {}
    df_tmp = df_test.reset_index(drop=True)
    for entity, grp in df_tmp.groupby(entity_col):
        idx = grp.index.values
        results[str(entity)] = compute_anomaly_metrics(
            y_true[idx], y_pred[idx], scores[idx], label=str(entity)
        )
    return results


def run_evaluation(
    scores: np.ndarray,
    y_pred: np.ndarray,
    y_true: Optional[np.ndarray],
    manifest: Dict[str, Any],
    df_test: Optional[pd.DataFrame] = None,
    mode_col: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full anomaly evaluation entry point.

    Returns evaluation_report and updates manifest.
    """
    ts_col = manifest.get("schema_config", {}).get("timestamp_column")
    entity_col = (manifest.get("entity_column")
                  or manifest.get("schema_config", {}).get("entity_column"))

    if y_true is None:
        print("[AnomalyEval] No ground truth labels — computing score distribution only.")
        report = {
            "mode": "unsupervised_score_only",
            "mean_score": round(float(scores.mean()), 4),
            "p99_score": round(float(np.percentile(scores, 99)), 4),
            "pct_flagged": round(float((y_pred == 1).mean()), 4),
        }
    else:
        report = compute_anomaly_metrics(y_true, y_pred, scores)

        # Detection latency
        if df_test is not None and ts_col and ts_col in df_test.columns:
            latency = compute_detection_latency(
                pd.Series(y_true), pd.Series(y_pred), df_test[ts_col]
            )
            report["detection_latency"] = latency

        # G-07 Fix: Per-entity breakdown
        if entity_col and df_test is not None and entity_col in df_test.columns:
            report["per_entity"] = per_entity_anomaly_metrics(
                df_test, y_true, y_pred, scores, entity_col
            )

        # Per-mode breakdown
        if mode_col and df_test is not None and mode_col in df_test.columns:
            per_mode = {}
            for mode, grp_idx in df_test.groupby(mode_col).groups.items():
                per_mode[str(mode)] = compute_anomaly_metrics(
                    y_true[grp_idx.values - df_test.index[0]],
                    y_pred[grp_idx.values - df_test.index[0]],
                    scores[grp_idx.values - df_test.index[0]],
                    label=str(mode),
                )
            report["per_mode"] = per_mode

    manifest.setdefault("results", {})
    manifest["results"]["anomaly_evaluation"] = report
    return report
