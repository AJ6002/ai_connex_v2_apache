"""
aiconnex_agent/scout/recipe_catalog_builder.py
================================================
Analyzes a compiled CSV produced by the UnifiedCompiler and generates:
  1. dataset_card     — Name, Industry, Domain, Sampling, Rows, Columns, Date Range, Targets
  2. schema_map       — {column: "datetime"|"numeric"|"categorical"|"text"}
  3. target_candidates — continuous numeric columns suitable for regression/forecast
  4. feature_catalog   — Detailed per-column metadata (type, role, operational description, units)
  5. problem_candidates — ML task family suitability assessments
  6. recipes          — ordered list of AnalyticalRecipe objects (the user picks one)
  7. branching_hints  — available analytical branches (Water Quality, Forecasting, Anomaly, etc.)

This module is the bridge between raw compiled data and HITL-ready intelligence.
No LLM calls — pure pandas statistical analysis. Deterministic and fast.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Number of unique values below which a numeric column is treated as categorical
_CATEGORICAL_CARDINALITY_THRESHOLD = 20
# Minimum coefficient of variation to qualify as a regression target
_MIN_CV_FOR_REGRESSION_TARGET = 0.05
# Columns that are almost always IDs/metadata — excluded from targets
_EXCLUDE_PATTERNS = {"id", "index", "row", "key", "company", "name", "type", "status"}

# Domain dictionary for common industrial parameter descriptions & units
_PARAMETER_DESCRIPTIONS: Dict[str, Tuple[str, str]] = {
    "tds": ("Total Dissolved Solids (Salinity)", "mg/L"),
    "cod": ("Chemical Oxygen Demand (Organic Load)", "mg/L"),
    "ph": ("Acidity / Alkalinity Level", "pH"),
    "ss": ("Suspended Solids", "mg/L"),
    "volume": ("Effluent Flow Volume", "m3"),
    "an": ("Ammoniacal Nitrogen", "mg/L"),
    "bod": ("Biochemical Oxygen Demand", "mg/L"),
    "temp": ("Temperature", "°C"),
    "turbidity": ("Water Clarity / Turbidity", "NTU"),
}


def _infer_dtype(series) -> str:
    """Infer semantic dtype for a pandas Series."""
    import pandas as pd
    col_lower = series.name.lower()

    if "date" in col_lower or "time" in col_lower or "dt" in col_lower:
        try:
            pd.to_datetime(series.dropna().head(50))
            return "datetime"
        except Exception:
            pass

    if pd.api.types.is_numeric_dtype(series):
        nuniq = series.nunique()
        if nuniq <= _CATEGORICAL_CARDINALITY_THRESHOLD:
            return "categorical"
        return "numeric"

    coerced = pd.to_numeric(series, errors="coerce")
    if coerced.notna().mean() > 0.85:
        return "numeric"

    nuniq = series.nunique()
    if nuniq <= _CATEGORICAL_CARDINALITY_THRESHOLD:
        return "categorical"
    return "text"


def _coefficient_of_variation(series) -> float:
    """Return std/mean; 0.0 if mean is zero or all NaN."""
    import numpy as np
    clean = series.dropna()
    if len(clean) == 0:
        return 0.0
    mean = clean.mean()
    if abs(mean) < 1e-9:
        return 0.0
    return float(clean.std() / abs(mean))


def _is_excluded(col_name: str) -> bool:
    col_lower = col_name.lower()
    return any(pat in col_lower for pat in _EXCLUDE_PATTERNS)


def _detect_time_series(df, schema_map: Dict[str, str]) -> bool:
    has_dt = any(v == "datetime" for v in schema_map.values())
    return has_dt and len(df) > 50


def build_recipe_catalog(csv_path: str) -> Dict[str, Any]:
    """
    Analyze the compiled CSV at csv_path and return a complete intelligence dict:
      dataset_card, schema_map, target_candidates, problem_candidates,
      feature_catalog, recipes, branching_hints
    """
    import pandas as pd
    from pathlib import Path

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Compiled CSV not found: {csv_path}")

    logger.info(f"[RecipeCatalogBuilder] Analyzing {path.name} ({path.stat().st_size // 1024} KB)")
    df = pd.read_csv(path, low_memory=False)
    rows, cols = len(df), len(df.columns)

    # ── 1. Schema Map ──────────────────────────────────────────────────────────
    schema_map: Dict[str, str] = {}
    for col in df.columns:
        schema_map[col] = _infer_dtype(df[col])

    # ── 2. Target Candidates ──────────────────────────────────────────────────
    target_candidates: List[str] = []
    for col, dtype in schema_map.items():
        if dtype == "numeric" and not _is_excluded(col):
            cv = _coefficient_of_variation(df[col])
            if cv >= _MIN_CV_FOR_REGRESSION_TARGET:
                target_candidates.append(col)

    # ── 3. Date Range ─────────────────────────────────────────────────────────
    date_range = "N/A"
    dt_cols = [c for c, d in schema_map.items() if d == "datetime"]
    if dt_cols:
        try:
            dt_series = pd.to_datetime(df[dt_cols[0]].dropna())
            date_range = f"{dt_series.min().strftime('%b %Y')} - {dt_series.max().strftime('%b %Y')}"
        except Exception:
            pass

    # ── 4. Dataset Card ───────────────────────────────────────────────────────
    dataset_card = {
        "dataset_name": path.stem,
        "industry": "Industrial Effluent & Wastewater",
        "domain": "Water Quality & Environmental Monitoring",
        "sampling_rate": "Daily Laboratory Measurements" if len(dt_cols) > 0 else "Batch Measurements",
        "rows": rows,
        "columns": cols,
        "date_range": date_range,
        "target_candidates": target_candidates,
    }

    # ── 5. Feature Catalog ────────────────────────────────────────────────────
    feature_catalog: Dict[str, Any] = {}
    for col, dtype in schema_map.items():
        col_lower = col.lower().strip()
        desc, units = _PARAMETER_DESCRIPTIONS.get(col_lower, (col, "unitless"))
        
        role = "Metadata / Identity" if _is_excluded(col) else ("Target Candidate" if col in target_candidates else "Feature")
        type_str = "Continuous Numeric" if dtype == "numeric" else dtype.title()

        feature_catalog[col] = {
            "type": type_str,
            "role": role,
            "description": desc,
            "units": units,
        }

    # ── 6. Problem Candidates ─────────────────────────────────────────────────
    has_temporal = _detect_time_series(df, schema_map)
    has_targets = len(target_candidates) > 0

    problem_candidates = []
    if has_targets:
        problem_candidates.append({"family": "Regression", "confidence": 0.92})
    if has_temporal and has_targets:
        problem_candidates.append({"family": "Time_Series", "confidence": 0.85})
    problem_candidates.append({"family": "Anomaly", "confidence": 0.78})

    # ── 7. Recipe Catalog ─────────────────────────────────────────────────────
    recipes = []
    recipe_idx = 1

    target_scores: List[Tuple[str, float]] = []
    for col in target_candidates:
        cv = _coefficient_of_variation(df[col])
        conf = min(0.99, 0.70 + min(cv, 1.0) * 0.29)
        target_scores.append((col, round(conf, 2)))

    target_scores.sort(key=lambda x: x[1], reverse=True)

    # Regression recipes
    for col, conf in target_scores[:5]:
        recipes.append({
            "id": f"R{recipe_idx:03d}",
            "title": f"Predict {col}",
            "target": col,
            "task": "REGRESSION",
            "confidence": conf,
            "rationale": f"'{col}' shows sufficient variance (CV≥{_MIN_CV_FOR_REGRESSION_TARGET:.0%}) for supervised prediction"
        })
        recipe_idx += 1

    # Forecast recipe
    if has_temporal and target_scores:
        top_col, top_conf = target_scores[0]
        recipes.append({
            "id": f"R{recipe_idx:03d}",
            "title": f"Forecast {top_col} (Time-Series)",
            "target": top_col,
            "task": "FORECAST",
            "confidence": round(top_conf - 0.07, 2),
            "rationale": f"Datetime index detected — temporal forecasting of '{top_col}' is applicable"
        })
        recipe_idx += 1

    # Anomaly recipe
    recipes.append({
        "id": f"R{recipe_idx:03d}",
        "title": "Detect Dataset Anomalies & Outliers",
        "target": None,
        "task": "ANOMALY",
        "confidence": 0.78,
        "rationale": "Unsupervised anomaly detection applicable to all compiled datasets"
    })

    # ── 8. Branching Hints ───────────────────────────────────────────────────
    available_branches = []
    if has_targets:
        available_branches.append("Water Quality Prediction")
    if has_temporal:
        available_branches.append("Forecasting")
    available_branches.append("Anomaly Detection")
    available_branches.append("Compliance Monitoring")

    branching_hints = {
        "available_branches": available_branches
    }

    logger.info(
        f"[RecipeCatalogBuilder] Generated {len(recipes)} recipes, "
        f"{len(target_candidates)} target candidates, {len(schema_map)} schema columns"
    )

    return {
        "dataset_card": dataset_card,
        "schema_map": schema_map,
        "target_candidates": target_candidates,
        "problem_candidates": problem_candidates,
        "feature_catalog": feature_catalog,
        "recipes": recipes,
        "branching_hints": branching_hints,
    }
