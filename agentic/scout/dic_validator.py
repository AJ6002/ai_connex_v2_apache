"""
aiconnex_agent/scout/dic_validator.py - Post-Compile DIC Completeness Validator
=================================================================================
Validates the completeness of DatasetIntelligenceContract (DIC) output post-compilation.
Detects empty or partially populated fields (Issue 6) and emits actionable warnings.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class DICValidator:
    """Post-compile completeness validator for DatasetIntelligenceContract."""

    def validate(self, dic_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate DIC completeness.

        Returns:
            Tuple of (is_valid, list_of_warning_messages)
        """
        warnings: List[str] = []
        is_valid = True

        identity = dic_dict.get("dataset_identity", {})
        compiled = dic_dict.get("compiled_dataset", {})
        stats = dic_dict.get("statistics", {})
        quality = dic_dict.get("quality_report", {})

        # 1. Dataset Identity Check
        if not identity.get("name"):
            warnings.append("Dataset identity name is missing or empty")

        # 2. Record / Table Count Check
        rows = compiled.get("rows", 0)
        tables = compiled.get("tables", 0)
        if rows == 0 and tables == 0:
            warnings.append("Compiled dataset contains 0 rows and 0 tables")
            is_valid = False

        # 3. Statistics Completeness Check
        missing = stats.get("missing_values", {})
        if not missing and rows > 0:
            warnings.append("Column missing_values statistics were not computed")

        # 4. Quality Report Check
        if not quality.get("cartesian_guard_passed", True):
            warnings.append("Cartesian product explosion guard triggered during join compilation")

        logger.info(f"[DICValidator] Validation result: valid={is_valid}, warnings={len(warnings)}")
        return is_valid, warnings
