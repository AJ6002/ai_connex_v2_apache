"""
serving.py — Batch & Real-Time Inference Module (Sprint 4 / G-09 Fix)
====================================================================
Loads a trained pipeline (model pickle, scaler pickle, manifest) and
executes batch or real-time inference on new feature DataFrames or CSV files.
"""

from __future__ import annotations
import os
import json
import pickle
from typing import Dict, Any, Optional, Union
import pandas as pd
import numpy as np


class Predictor:
    """
    Production inference engine.

    Usage:
        predictor = Predictor.from_manifest("training_manifest_run123.json")
        df_preds = predictor.predict_df(df_new)
        predictor.predict_csv("new_input.csv", "predictions_out.csv")
    """

    def __init__(
        self,
        model: Any,
        scaler: Optional[Any] = None,
        feature_cols: Optional[list] = None,
        target_col: Optional[str] = None,
        manifest: Optional[Dict[str, Any]] = None,
    ):
        self.model = model
        self.scaler = scaler
        self.feature_cols = feature_cols or []
        self.target_col = target_col
        self.manifest = manifest or {}

    @classmethod
    def from_manifest(cls, manifest_path: str) -> "Predictor":
        """Factory constructor that reads all artifacts from a manifest state file."""
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        training_results = manifest.get("training_results", {})
        model_path  = training_results.get("model_path")
        scaler_path = training_results.get("scaler_path")
        schema_cfg  = manifest.get("schema_config", {})
        feature_cols = schema_cfg.get("final_features") or manifest.get("features_config", {}).get("feature_names", [])

        target_col = manifest.get("label_contract", {}).get("target_column") or manifest.get("target_column")

        if not model_path or not os.path.exists(model_path):
            raise FileNotFoundError(f"Model pickle not found at {model_path}")

        with open(model_path, "rb") as f:
            model = pickle.load(f)

        scaler = None
        if scaler_path and os.path.exists(scaler_path):
            with open(scaler_path, "rb") as f:
                scaler = pickle.load(f)

        return cls(model=model, scaler=scaler, feature_cols=feature_cols, target_col=target_col, manifest=manifest)

    def predict_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run inference on a pandas DataFrame.
        Applies target dropping, feature selection, NaN median filling, scaling, and prediction.
        """
        df_out = df.copy()

        # Isolate features
        if self.feature_cols and all(c in df.columns for c in self.feature_cols):
            X_df = df[self.feature_cols]
        else:
            # Fallback: select numeric columns excluding target
            drop_cols = [self.target_col] if self.target_col and self.target_col in df.columns else []
            X_df = df.drop(columns=drop_cols, errors="ignore").select_dtypes(include=[np.number])

        X = X_df.fillna(X_df.median().fillna(0)).values

        if self.scaler is not None:
            X = self.scaler.transform(X)

        # Predict
        preds = self.model.predict(X)

        # Handle anomaly detection output mapping
        model_name = self.model.__class__.__name__.lower()
        if "isolationforest" in model_name:
            # -1 = anomaly, +1 = normal -> map to binary flag (1=anomaly, 0=normal)
            df_out["prediction_anomaly"] = np.where(preds == -1, 1, 0)
            if hasattr(self.model, "decision_function"):
                df_out["anomaly_score"] = -self.model.decision_function(X)
        else:
            df_out["prediction"] = preds

        return df_out

    def predict_csv(self, input_csv: str, output_csv: str) -> str:
        """Run batch inference on an input CSV and save predictions to output CSV."""
        if not os.path.exists(input_csv):
            raise FileNotFoundError(f"Input file not found: {input_csv}")

        df = pd.read_csv(input_csv)
        df_out = self.predict_df(df)

        os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
        df_out.to_csv(output_csv, index=False)
        print(f"[Predictor] Batch inference complete ({len(df_out)} rows) → {output_csv}")
        return output_csv
