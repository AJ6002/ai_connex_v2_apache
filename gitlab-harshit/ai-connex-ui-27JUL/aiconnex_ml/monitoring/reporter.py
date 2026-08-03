"""
reporter.py — Report generation: JSON, Markdown, and CSV summaries
===================================================================
Generates structured reports from the manifest results dict for:
  - Dashboard display (JSON)
  - Human-readable summaries (Markdown)
  - Experiment tracking (CSV leaderboard)
"""

from __future__ import annotations
import json
import os
from typing import Dict, Any
from datetime import datetime
import numpy as np


def generate_json_report(manifest: Dict[str, Any], output_path: str) -> str:
    """Save the full results section of the manifest as a JSON report."""
    report = {
        "pipeline_run_id": manifest.get("pipeline_run_id"),
        "ml_task": manifest.get("ml_task"),
        "timestamp": datetime.utcnow().isoformat(),
        "best_algorithm": manifest.get("results", {}).get("best_algorithm"),
        "best_params": manifest.get("results", {}).get("best_params"),
        "evaluation": manifest.get("results", {}).get(
            "evaluation",
            manifest.get("results", {}).get("anomaly_evaluation", {})
        ),
        "threshold_calibration": manifest.get("results", {}).get("threshold_calibration"),
        "robustness": manifest.get("results", {}).get("robustness"),
        "validation_gates": manifest.get("validation_results"),
        "model_path": manifest.get("paths", {}).get("best_model"),
        "scaler_path": manifest.get("paths", {}).get("scaler"),
        "completed_steps": manifest.get("completed_steps", []),
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[Reporter] JSON report saved: {output_path}")
    return output_path


def generate_markdown_report(manifest: Dict[str, Any], output_path: str) -> str:
    """Generate a human-readable Markdown summary of the training run."""
    run_id = manifest.get("pipeline_run_id", "unknown")
    ml_task = manifest.get("ml_task", "unknown")
    best_algo = manifest.get("results", {}).get("best_algorithm", "unknown")
    eval_results = manifest.get("results", {}).get(
        "evaluation",
        manifest.get("results", {}).get("anomaly_evaluation", {})
    )
    vg1 = manifest.get("validation_results", {}).get("vg_1", {})
    vg2 = manifest.get("validation_results", {}).get("vg_2", {})

    lines = [
        f"# AIConnex ML Pipeline Report",
        f"",
        f"**Run ID:** `{run_id}`  ",
        f"**Task:** `{ml_task}`  ",
        f"**Timestamp:** `{datetime.utcnow().isoformat()}`",
        f"",
        f"---",
        f"## Best Model",
        f"- **Algorithm:** {best_algo}",
        f"- **Model Path:** `{manifest.get('paths', {}).get('best_model', 'N/A')}`",
        f"",
        f"## Evaluation Results",
    ]

    if ml_task == "regression":
        test_m = eval_results.get("test", {})
        lines += [
            f"| Metric | Test Set |",
            f"|--------|----------|",
            f"| RMSE | {test_m.get('rmse', 'N/A')} |",
            f"| MAE  | {test_m.get('mae', 'N/A')} |",
            f"| MAPE | {test_m.get('mape', 'N/A')} |",
            f"| R²   | {test_m.get('r2', 'N/A')} |",
        ]
        if test_m.get("rul_asymmetric_score") is not None:
            lines.append(f"| RUL Score | {test_m['rul_asymmetric_score']} |")
    elif ml_task == "anomaly":
        lines += [
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Precision | {eval_results.get('precision', 'N/A')} |",
            f"| Recall    | {eval_results.get('recall', 'N/A')} |",
            f"| F1        | {eval_results.get('f1', 'N/A')} |",
            f"| PR-AUC    | {eval_results.get('pr_auc', 'N/A')} |",
            f"| FAR/week  | {eval_results.get('false_alarm_rate_per_week_estimate', 'N/A')} |",
        ]

    # G-11 Fix: Generate and embed residual chart if plot artifacts exist
    chart_path = os.path.join(os.path.dirname(os.path.abspath(output_path)), f"{run_id}_residual.png")
    if _try_generate_residual_plot(eval_results, chart_path):
        lines += [
            f"",
            f"## Performance Visualizations",
            f"![Residual Plot]({os.path.basename(chart_path)})",
        ]

    lines += [
        f"",
        f"## Validation Gates",
        f"- **VG_1 (Data):** {'✅ PASS' if vg1.get('passed') else '❌ FAIL'}",
        f"- **VG_2 (Model):** {'✅ PASS' if vg2.get('passed') else '❌ FAIL'}",
        f"",
        f"## Completed Steps",
    ]
    for step in manifest.get("completed_steps", []):
        lines.append(f"- [x] {step}")

    content = "\n".join(lines)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Reporter] Markdown report saved: {output_path}")
    return output_path


def _try_generate_residual_plot(eval_results: Dict[str, Any], chart_path: str) -> bool:
    """Generate a residual scatter plot if matplotlib is installed and prediction arrays exist."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        y_true = eval_results.get("y_test_true") or eval_results.get("test", {}).get("y_test_true")
        y_pred = eval_results.get("y_test_pred") or eval_results.get("test", {}).get("y_test_pred")

        if y_true is None or y_pred is None:
            return False

        residuals = np.array(y_true) - np.array(y_pred)
        plt.figure(figsize=(6, 4))
        plt.scatter(y_pred, residuals, alpha=0.5, color="#1f77b4")
        plt.axhline(0, color="red", linestyle="--")
        plt.xlabel("Predicted Values")
        plt.ylabel("Residuals (Actual - Predicted)")
        plt.title("Model Residual Distribution")
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150)
        plt.close()
        return True
    except Exception:
        return False
