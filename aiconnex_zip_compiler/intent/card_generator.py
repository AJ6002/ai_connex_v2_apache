"""
intent/card_generator.py — Lightweight Dataset Card Generator
==============================================================
Generates a DatasetCard by inspecting file inventory and sniffing column headers
from the first few files. Runs BEFORE the full plugin pipeline — must be fast
and non-destructive (no full CSV parsing, just header sampling).
"""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .models import DatasetCard

logger = logging.getLogger(__name__)

# Domain detection patterns
DOMAIN_SIGNALS = {
    "aerospace_predictive_maintenance": [
        "sensor_", "op_setting", "unit_id", "cycle", "engine", "turbofan", "cmapss",
    ],
    "bearing_health_monitoring": [
        "acc_", "vibration", "bearing", "rms", "kurtosis", "crest",
    ],
    "renewable_energy": [
        "dc_power", "ac_power", "irradiation", "solar", "inverter", "plant_id", "module_temperature",
    ],
    "industrial_scada": [
        "pressure", "temperature", "compressor", "discharge", "suction", "motor_current", "dpr",
    ],
    "battery_degradation": [
        "capacity", "voltage_measured", "current_measured", "discharge", "soc", "soh",
    ],
    "general_tabular": [],
}

# Time column patterns
TIME_PATTERNS = re.compile(
    r"^(time|date|datetime|timestamp|time_stamp|date_time|ts|clock|period|cycle|time_cycles)$",
    re.IGNORECASE,
)

# Entity/group key patterns
ENTITY_PATTERNS = re.compile(
    r"^(unit_id|device_id|asset_id|plant_id|machine_id|sensor_id|bearing_id|engine_id|group_id)$",
    re.IGNORECASE,
)

# Operating condition patterns in filenames
CONDITION_PATTERNS = re.compile(
    r"(fd\d{3}|fd_\d{3}|condition_\d+|mode_\d+|exp_\d+|bearing\d+_\d+)",
    re.IGNORECASE,
)


class CardGenerator:
    """
    Generates a DatasetCard from file inventory and lightweight header sampling.
    Does NOT run full parsing — only reads first few lines of representative files.
    """

    def generate(
        self,
        dataset_name: str,
        inventory: List[Dict[str, str]],
        base_dir: Optional[Path] = None,
    ) -> DatasetCard:
        """
        Generate DatasetCard from inventory metadata and header sniffing.

        Parameters
        ----------
        dataset_name : str
            Name of the input archive/directory.
        inventory : list of dicts
            Each dict has: filepath, relative_path, format_ext, size_bytes
        base_dir : Path, optional
            Base directory for resolving file paths during header sniffing.
        """
        # Collect file extensions and filenames
        extensions: Set[str] = set()
        filenames: List[str] = []
        csv_files: List[Path] = []
        excel_files: List[Path] = []
        total_size = 0

        for item in inventory:
            ext = item.get("format_ext", "")
            extensions.add(ext)
            fname = item.get("relative_path", "")
            filenames.append(fname)
            total_size += item.get("size_bytes", 0)

            fp = Path(item.get("filepath", ""))
            if ext in (".csv", ".txt") and fp.exists():
                csv_files.append(fp)
            elif ext in (".xlsx", ".xls") and fp.exists():
                excel_files.append(fp)

        # Sniff headers from up to 3 CSV/TXT files
        all_headers: List[str] = []
        row_estimates = 0
        for fp in csv_files[:3]:
            headers, rows = self._sniff_csv_headers(fp)
            all_headers.extend(headers)
            row_estimates += rows

        # Detect sheets from Excel files
        detected_sheets: List[str] = []
        for fp in excel_files[:2]:
            sheets = self._sniff_excel_sheets(fp)
            detected_sheets.extend(sheets)

        # Classify columns
        entity_keys = [h for h in all_headers if ENTITY_PATTERNS.match(h)]
        time_keys = [h for h in all_headers if TIME_PATTERNS.match(h)]
        sensor_columns = [h for h in all_headers if h not in entity_keys and h not in time_keys]

        # Detect operating conditions from filenames
        detected_conditions = self._detect_conditions(filenames)

        # Detect domain
        domain = self._detect_domain(all_headers, filenames, extensions)

        # Determine dataset type
        dataset_type = self._classify_type(
            file_count=len(inventory),
            conditions=detected_conditions,
            sheets=detected_sheets,
            extensions=extensions,
            csv_count=len(csv_files),
        )

        # Generate summary
        summary = self._generate_summary(
            domain, dataset_type, len(inventory), detected_conditions, detected_sheets
        )

        return DatasetCard(
            dataset_name=dataset_name,
            domain=domain,
            dataset_type=dataset_type,
            entity_keys=list(set(entity_keys)),
            time_keys=list(set(time_keys)),
            sensor_columns=list(set(sensor_columns))[:20],
            detected_conditions=detected_conditions,
            detected_sheets=detected_sheets,
            file_count=len(inventory),
            total_rows_estimate=row_estimates,
            summary=summary,
        )

    def _sniff_csv_headers(self, filepath: Path, max_rows: int = 5) -> Tuple[List[str], int]:
        """Read first few lines of a CSV/TXT to extract headers and estimate rows."""
        headers: List[str] = []
        row_count = 0
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                # Count total lines for row estimate
                for i, line in enumerate(f):
                    if i == 0:
                        # Try to parse header
                        sniffer_sample = line
                    row_count += 1
                    if i > 10000:
                        # Estimate based on file size
                        avg_line_size = filepath.stat().st_size / (i + 1)
                        row_count = int(filepath.stat().st_size / max(avg_line_size, 1))
                        break

            # Parse header line
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
                if first_row:
                    # Check if this looks like a header (not all numeric)
                    numeric_count = sum(1 for v in first_row if self._is_numeric(v))
                    if numeric_count < len(first_row) * 0.8:
                        headers = [h.strip().lower().replace(" ", "_") for h in first_row]
        except Exception as e:
            logger.debug(f"[CardGenerator] Header sniff failed for {filepath.name}: {e}")

        return headers, max(0, row_count - 1)

    def _sniff_excel_sheets(self, filepath: Path) -> List[str]:
        """Get sheet names from an Excel file without loading data."""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            sheets = wb.sheetnames
            wb.close()
            return sheets
        except Exception:
            try:
                import pandas as pd
                xls = pd.ExcelFile(filepath)
                return xls.sheet_names
            except Exception:
                return []

    def _detect_conditions(self, filenames: List[str]) -> List[str]:
        """Detect operating conditions from filename patterns."""
        conditions: Set[str] = set()
        for fname in filenames:
            matches = CONDITION_PATTERNS.findall(fname)
            for m in matches:
                conditions.add(m.upper().replace("_", ""))
        return sorted(conditions)

    def _detect_domain(
        self, headers: List[str], filenames: List[str], extensions: Set[str]
    ) -> str:
        """Classify domain from column headers and file patterns."""
        combined_text = " ".join(headers + filenames).lower()

        scores: Dict[str, int] = {}
        for domain, signals in DOMAIN_SIGNALS.items():
            if not signals:
                continue
            score = sum(1 for s in signals if s in combined_text)
            if score > 0:
                scores[domain] = score

        if scores:
            return max(scores, key=scores.get)
        return "general_tabular"

    def _classify_type(
        self,
        file_count: int,
        conditions: List[str],
        sheets: List[str],
        extensions: Set[str],
        csv_count: int,
    ) -> str:
        """Classify dataset structural type."""
        if len(conditions) >= 2:
            return "multi_operating_condition_time_series"
        if len(sheets) >= 2:
            return "multi_sheet_workbook"
        if file_count > 100 and csv_count > 50:
            return "high_frequency_snapshot_collection"
        if ".mat" in extensions:
            return "matlab_struct_archive"
        if ".h5" in extensions or ".hdf5" in extensions:
            return "hdf5_telemetry_archive"
        if csv_count >= 2:
            return "multi_table_relational"
        return "single_table"

    def _generate_summary(
        self,
        domain: str,
        dataset_type: str,
        file_count: int,
        conditions: List[str],
        sheets: List[str],
    ) -> str:
        """Generate plain-language summary for the TUI."""
        domain_labels = {
            "aerospace_predictive_maintenance": "Aerospace engine sensor telemetry",
            "bearing_health_monitoring": "Bearing vibration health data",
            "renewable_energy": "Solar/wind power generation data",
            "industrial_scada": "Industrial compressor SCADA readings",
            "battery_degradation": "Battery charge-discharge cycling data",
            "general_tabular": "Tabular dataset",
        }
        domain_label = domain_labels.get(domain, domain.replace("_", " ").title())

        if conditions:
            return f"{domain_label} with {len(conditions)} operating conditions ({', '.join(conditions[:4])})"
        if sheets:
            return f"{domain_label} workbook with {len(sheets)} data sheets ({', '.join(sheets[:3])})"
        if file_count > 100:
            return f"{domain_label} — {file_count} snapshot files"
        return f"{domain_label} — {file_count} file(s)"

    @staticmethod
    def _is_numeric(val: str) -> bool:
        try:
            float(val.strip())
            return True
        except (ValueError, AttributeError):
            return False
