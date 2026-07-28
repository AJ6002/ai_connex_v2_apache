"""
intent/classifier.py - Heuristic Intent Classifier
====================================================
Analyzes a DatasetCard and determines which modeling directions are feasible.
Generates 2-4 IntentOptions for the user to pick from.

This is a deterministic heuristic engine (no LLM call). It inspects:
  - Domain classification
  - Dataset type (multi-condition, multi-sheet, snapshot, etc.)
  - Detected entity/time keys
  - File/condition count

Rules:
  - If only 1 feasible option exists -> return it (compiler proceeds without halting)
  - If 2+ feasible options -> return them (terminal prompt halts for user input)
"""

from __future__ import annotations

import logging
from typing import List

from .models import DatasetCard, IntentOption

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Determines feasible modeling directions from a DatasetCard.
    Returns IntentOptions written in plain language for field engineers.
    """

    def classify(self, card: DatasetCard) -> List[IntentOption]:
        """
        Analyze DatasetCard and return feasible IntentOptions.
        Options are ordered: most common/recommended first.
        """
        options: List[IntentOption] = []

        # -- Multi-Operating Condition datasets (C-MAPSS, FEMTO) ------------
        if card.dataset_type == "multi_operating_condition_time_series" and len(card.detected_conditions) >= 2:
            options.append(IntentOption(
                option_id="unified_all_conditions",
                label="Unified model across all operating conditions",
                description=(
                    f"Combines {', '.join(card.detected_conditions[:4])} into a single master dataset. "
                    "Best for general-purpose deployment across all regimes."
                ),
                is_default=True,
            ))
            options.append(IntentOption(
                option_id="separate_per_condition",
                label="Separate model per operating condition",
                description=(
                    f"Builds {len(card.detected_conditions)} individual datasets "
                    f"({', '.join(card.detected_conditions[:4])}). "
                    "Best when conditions have distinct physical baselines."
                ),
            ))
            return options

        # -- Multi-Sheet Workbook (SCADA Excel) ------------------------------
        if card.dataset_type == "multi_sheet_workbook" and len(card.detected_sheets) >= 2:
            # For SCADA: sensor-focused vs combined
            if card.domain == "industrial_scada":
                options.append(IntentOption(
                    option_id="failure_prediction",
                    label="Predict equipment failure",
                    description="Uses sensor readings to alert you before breakdowns happen.",
                    is_default=True,
                ))
                options.append(IntentOption(
                    option_id="anomaly_detection",
                    label="Detect unusual behavior",
                    description="Spots abnormal sensor patterns that may indicate developing problems.",
                ))
                options.append(IntentOption(
                    option_id="forecasting",
                    label="Forecast future readings",
                    description="Predicts next-period sensor values from historical trends.",
                ))
            else:
                # Generic multi-sheet
                options.append(IntentOption(
                    option_id="primary_sheet_model",
                    label="Build model from primary data sheet",
                    description=f"Uses the main data sheet ({card.detected_sheets[0]}) for modeling.",
                    is_default=True,
                ))
                options.append(IntentOption(
                    option_id="combined_sheets_model",
                    label="Combine all sheets into one model",
                    description=f"Merges {len(card.detected_sheets)} sheets by shared date/time column.",
                ))
            return options

        # -- High-Frequency Snapshot (Bearings, IMS, FEMTO) ------------------
        if card.dataset_type == "high_frequency_snapshot_collection":
            options.append(IntentOption(
                option_id="failure_prediction",
                label="Predict equipment failure",
                description="Computes health indicators from vibration data to predict remaining life.",
                is_default=True,
            ))
            options.append(IntentOption(
                option_id="anomaly_detection",
                label="Detect unusual vibration patterns",
                description="Identifies abnormal signals that deviate from healthy baselines.",
            ))
            return options

        # -- Multi-Table Relational (Solar, multi-CSV) -----------------------
        if card.dataset_type == "multi_table_relational":
            if card.domain == "renewable_energy":
                options.append(IntentOption(
                    option_id="forecasting",
                    label="Forecast power generation",
                    description="Predicts future solar/wind output from weather and historical data.",
                    is_default=True,
                ))
                options.append(IntentOption(
                    option_id="anomaly_detection",
                    label="Detect inverter/plant anomalies",
                    description="Spots underperforming equipment relative to weather conditions.",
                ))
            else:
                options.append(IntentOption(
                    option_id="anomaly_detection",
                    label="Detect unusual behavior",
                    description="Identifies abnormal patterns across related data tables.",
                    is_default=True,
                ))
                options.append(IntentOption(
                    option_id="forecasting",
                    label="Forecast future values",
                    description="Predicts next-period values from time-series history.",
                ))
            return options

        # -- MATLAB Struct / HDF5 (Battery, complex struct) ------------------
        if card.dataset_type in ("matlab_struct_archive", "hdf5_telemetry_archive"):
            if card.domain == "battery_degradation":
                options.append(IntentOption(
                    option_id="failure_prediction",
                    label="Predict battery end-of-life",
                    description="Estimates remaining useful life from capacity degradation curves.",
                    is_default=True,
                ))
            else:
                options.append(IntentOption(
                    option_id="failure_prediction",
                    label="Predict equipment failure",
                    description="Uses degradation patterns to estimate remaining useful life.",
                    is_default=True,
                ))
            options.append(IntentOption(
                option_id="anomaly_detection",
                label="Detect degradation anomalies",
                description="Spots abnormal degradation rates compared to fleet baselines.",
            ))
            return options

        # -- Single Table / General Tabular (fallback) -----------------------
        # Only one feasible direction - no halt needed
        options.append(IntentOption(
            option_id="auto_model",
            label="Build predictive model",
            description="Standard tabular regression/classification on available features.",
            is_default=True,
        ))
        return options
