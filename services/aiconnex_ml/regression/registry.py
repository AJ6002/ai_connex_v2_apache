"""
registry.py — REGRESSION_REGISTRY: all supported regression algorithms
=======================================================================
Maps DAG algorithm names (from algorithm_families.xlsx) to sklearn-compatible
model classes and their default hyperparameter search spaces for HPO.

Each entry:
  "AlgorithmName": {
      "class":      model class,
      "params":     hyperparameter grid for RandomizedSearchCV,
      "requires":   optional package guard,
      "notes":      usage note,
  }
"""

from __future__ import annotations
from typing import Dict, Any

import numpy as np
from sklearn.linear_model import (
    LinearRegression, Ridge, Lasso, ElasticNet,
)
from sklearn.ensemble import (
    RandomForestRegressor, GradientBoostingRegressor, BaggingRegressor,
)
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.cross_decomposition import PLSRegression


def _xgb_class():
    from xgboost import XGBRegressor
    return XGBRegressor

def _lgbm_class():
    from lightgbm import LGBMRegressor
    return LGBMRegressor

def _catboost_class():
    from catboost import CatBoostRegressor
    return CatBoostRegressor


REGRESSION_REGISTRY: Dict[str, Any] = {

    # ── Linear family ──────────────────────────────────────────────────────────
    "Linear Regression": {
        "class": LinearRegression,
        "params": {},
        "notes": "Baseline. No hyperparameters to tune.",
    },
    "Ridge Regression": {
        "class": Ridge,
        "params": {"alpha": np.logspace(-3, 3, 50)},
        "notes": "L2 regularization.",
    },
    "Lasso Regression": {
        "class": Lasso,
        "params": {"alpha": np.logspace(-3, 3, 50), "max_iter": [5000]},
        "notes": "L1 regularization — induces feature sparsity.",
    },
    "ElasticNet": {
        "class": ElasticNet,
        "params": {
            "alpha": np.logspace(-3, 2, 30),
            "l1_ratio": np.linspace(0.1, 0.9, 9),
            "max_iter": [5000],
        },
        "notes": "L1+L2 combined. Use when both regularization effects needed.",
    },

    # ── Tree ensembles ─────────────────────────────────────────────────────────
    "Random Forest": {
        "class": RandomForestRegressor,
        "params": {
            "n_estimators": [100, 200, 300],
            "max_depth": [None, 5, 10, 20],
            "min_samples_split": [2, 5, 10],
            "max_features": ["sqrt", "log2", 0.5],
        },
        "notes": "Robust ensemble baseline.",
    },
    "XGBoost": {
        "class": _xgb_class,
        "params": {
            "n_estimators": [100, 200, 300, 500],
            "max_depth": [3, 5, 7, 9],
            "learning_rate": [0.01, 0.05, 0.1, 0.2],
            "subsample": [0.6, 0.8, 1.0],
            "colsample_bytree": [0.6, 0.8, 1.0],
            "reg_alpha": [0, 0.1, 1.0],
            "reg_lambda": [1.0, 5.0, 10.0],
        },
        "requires": "xgboost",
        "notes": "Primary default for regression. Supports monotonic_constraints.",
    },
    "LightGBM": {
        "class": _lgbm_class,
        "params": {
            "n_estimators": [100, 300, 500],
            "max_depth": [-1, 5, 10],
            "learning_rate": [0.01, 0.05, 0.1],
            "num_leaves": [31, 63, 127],
            "subsample": [0.7, 0.9, 1.0],
            "colsample_bytree": [0.7, 0.9, 1.0],
        },
        "requires": "lightgbm",
        "notes": "Fast and memory-efficient. Good for large datasets.",
    },
    "CatBoost": {
        "class": _catboost_class,
        "params": {
            "iterations": [100, 300, 500],
            "learning_rate": [0.01, 0.05, 0.1],
            "depth": [4, 6, 8, 10],
        },
        "requires": "catboost",
        "notes": "Strong for datasets with categorical features.",
    },
    "Gradient Boosting": {
        "class": GradientBoostingRegressor,
        "params": {
            "n_estimators": [100, 200],
            "max_depth": [3, 5, 7],
            "learning_rate": [0.05, 0.1, 0.2],
            "subsample": [0.7, 1.0],
        },
        "notes": "sklearn native gradient boosting.",
    },

    # ── SVM / KNN ──────────────────────────────────────────────────────────────
    "SVR": {
        "class": SVR,
        "params": {
            "C": np.logspace(-1, 3, 20),
            "epsilon": [0.01, 0.1, 0.5],
            "kernel": ["rbf", "linear"],
        },
        "notes": "Effective for small-medium datasets. Scale features first.",
    },
    "KNN": {
        "class": KNeighborsRegressor,
        "params": {
            "n_neighbors": [3, 5, 7, 10, 15],
            "weights": ["uniform", "distance"],
            "metric": ["euclidean", "manhattan"],
        },
        "notes": "Simple but computationally expensive at inference time.",
    },

    # ── Neural Networks ────────────────────────────────────────────────────────
    "Neural Network": {
        "class": MLPRegressor,
        "params": {
            "hidden_layer_sizes": [(64,), (128,), (64, 32), (128, 64)],
            "activation": ["relu", "tanh"],
            "learning_rate_init": [0.001, 0.01],
            "max_iter": [500],
        },
        "notes": "sklearn MLP. For deep learning, use PyTorch/LSTM via custom trainer.",
    },
}


def get_algorithm(name: str) -> Dict[str, Any]:
    """
    Retrieve an algorithm entry from the registry by name.
    Raises KeyError if not found. Resolves lazy class loaders.
    """
    if name not in REGRESSION_REGISTRY:
        available = list(REGRESSION_REGISTRY.keys())
        raise KeyError(f"Regression algorithm '{name}' not found. Available: {available}")
    entry = REGRESSION_REGISTRY[name].copy()
    requires = entry.get("requires")
    if requires:
        try:
            __import__(requires)
        except ImportError:
            raise ImportError(f"Package '{requires}' required for algorithm '{name}' is not installed.")
    if callable(entry["class"]) and not isinstance(entry["class"], type):
        entry["class"] = entry["class"]()  # resolve lazy import
    return entry


def list_algorithms() -> list:
    """Return a list of all registered regression algorithm names."""
    return list(REGRESSION_REGISTRY.keys())
