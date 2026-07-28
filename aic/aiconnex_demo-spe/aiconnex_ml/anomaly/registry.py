"""
registry.py — ANOMALY_REGISTRY: all supported anomaly detection algorithms
===========================================================================
Maps DAG algorithm names (from algorithm_families.xlsx F3) to model classes
and their HPO parameter grids. Each entry declares which supervision_mode(s)
it is eligible for: 'unsupervised', 'semi_supervised', 'supervised'.

Always-available:
  - Statistical/rule-based methods (Z-score, IQR, CUSUM, EWMA)
"""

from __future__ import annotations
from typing import Dict, Any, List

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.covariance import EllipticEnvelope
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA


def _xgb_clf():
    from xgboost import XGBClassifier
    return XGBClassifier

def _rf_clf():
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier


ANOMALY_REGISTRY: Dict[str, Any] = {

    # ── Unsupervised ──────────────────────────────────────────────────────────
    "Isolation Forest": {
        "class": IsolationForest,
        "eligible_modes": ["unsupervised", "semi_supervised"],
        "score_method": "decision_function",  # higher = more normal
        "invert_score": True,                 # negate so higher = more anomalous
        "params": {
            "n_estimators": [100, 200, 300],
            "contamination": [0.01, 0.02, 0.05, 0.10],
            "max_features": [0.5, 0.8, 1.0],
        },
        "notes": "Primary default. Fast, scalable, good general purpose.",
    },
    "Local Outlier Factor": {
        "class": LocalOutlierFactor,
        "eligible_modes": ["unsupervised"],
        "score_method": "negative_outlier_factor_",
        "invert_score": True,
        "params": {
            "n_neighbors": [5, 10, 20, 30],
            "contamination": [0.01, 0.05, 0.10],
            "metric": ["euclidean", "manhattan"],
        },
        "notes": "Local density-based. Good for variable-density datasets.",
    },
    "LOF": {
        "class": LocalOutlierFactor,
        "eligible_modes": ["unsupervised"],
        "score_method": "negative_outlier_factor_",
        "invert_score": True,
        "params": {
            "n_neighbors": [5, 10, 20],
            "contamination": [0.01, 0.05],
        },
        "notes": "Alias for Local Outlier Factor.",
    },
    "Elliptic Envelope": {
        "class": EllipticEnvelope,
        "eligible_modes": ["unsupervised", "semi_supervised"],
        "score_method": "decision_function",
        "invert_score": True,
        "params": {
            "contamination": [0.01, 0.05, 0.10],
            "support_fraction": [0.8, 0.9, None],
        },
        "notes": "Assumes Gaussian distribution. Good for multivariate normal data.",
    },
    "DBSCAN": {
        "class": DBSCAN,
        "eligible_modes": ["unsupervised"],
        "score_method": None,  # labels_: -1 = outlier
        "invert_score": False,
        "params": {
            "eps": [0.3, 0.5, 0.7, 1.0],
            "min_samples": [5, 10, 20],
        },
        "notes": "Density clustering. Points in no cluster (label=-1) are anomalies.",
    },

    # ── Semi-Supervised ───────────────────────────────────────────────────────
    "One-class SVM": {
        "class": OneClassSVM,
        "eligible_modes": ["semi_supervised"],
        "score_method": "decision_function",
        "invert_score": True,
        "params": {
            "nu": [0.01, 0.05, 0.10, 0.20],
            "kernel": ["rbf", "linear"],
            "gamma": ["scale", "auto", 0.01, 0.1],
        },
        "notes": "Train on normal-only data. Suitable for medium-sized datasets.",
    },
    "PCA-based": {
        "class": PCA,
        "eligible_modes": ["semi_supervised"],
        "score_method": "reconstruction_error",  # custom
        "invert_score": False,
        "params": {
            "n_components": [0.90, 0.95, 0.99, 5, 10, 20],
        },
        "notes": "Reconstruction error as anomaly score. Interpretable.",
    },

    # ── Supervised ────────────────────────────────────────────────────────────
    "XGBoost": {
        "class": _xgb_clf,
        "eligible_modes": ["supervised"],
        "score_method": "predict_proba",
        "invert_score": False,
        "params": {
            "n_estimators": [100, 200, 300],
            "max_depth": [3, 5, 7],
            "learning_rate": [0.05, 0.1, 0.2],
            "scale_pos_weight": [1, 5, 10, 20],  # handles class imbalance
        },
        "requires": "xgboost",
        "notes": "Use when fault labels are available. scale_pos_weight for imbalance.",
    },
    "Random Forest": {
        "class": _rf_clf,
        "eligible_modes": ["supervised"],
        "score_method": "predict_proba",
        "invert_score": False,
        "params": {
            "n_estimators": [100, 200, 300],
            "max_depth": [None, 5, 10],
            "class_weight": ["balanced", "balanced_subsample", None],
        },
        "notes": "Robust fault classifier when labeled data is available.",
    },
}


def get_algorithm(name: str) -> Dict[str, Any]:
    """Retrieve and resolve an anomaly algorithm by name."""
    if name not in ANOMALY_REGISTRY:
        available = list(ANOMALY_REGISTRY.keys())
        raise KeyError(f"Anomaly algorithm '{name}' not in registry. Available: {available}")
    entry = ANOMALY_REGISTRY[name].copy()
    if callable(entry["class"]) and not isinstance(entry["class"], type):
        entry["class"] = entry["class"]()
    return entry


def filter_by_supervision(supervision_mode: str) -> List[str]:
    """Return algorithm names eligible for the given supervision_mode."""
    return [
        name for name, entry in ANOMALY_REGISTRY.items()
        if supervision_mode in entry.get("eligible_modes", [])
    ]
