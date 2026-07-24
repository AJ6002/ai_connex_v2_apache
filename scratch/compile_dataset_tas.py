"""
compile_dataset_tas.py — Standalone Compiler for Dataset-TAS.zip (DPR Route)
=============================================================================
Dedicated, standalone ingestion compiler for Dataset-TAS.zip.
Parses all 6 monthly CNG Compressor DPR Excel workbooks (January – June 2026),
dynamically resolves the Date header block, extracts daily operational logs,
adds provenance metadata, and outputs a continuous time-series CSV matrix.

Usage:
    python scratch/compile_dataset_tas.py
"""

from __future__ import annotations

import io
import os
import re
import sys
import zipfile
from pathlib import Path
import pandas as pd
import openpyxl


def compile_dataset_tas(
    zip_path: str | Path = "data/raw/Dataset-TAS.zip",
    output_dir: str | Path = "workspace_data/dataset_tas_compiled"
) -> Path:
    zip_file = Path(zip_path).resolve()
    out_dir = Path(output_dir).resolve()
    os.makedirs(out_dir, exist_ok=True)

    if not zip_file.exists():
        raise FileNotFoundError(f"Input archive not found: {zip_file}")

    print(f"=== Standalone Dataset-TAS Compiler (DPR Route) ===")
    print(f"Input Archive : {zip_file}")
    print(f"Output Dir    : {out_dir}")

    compiled_dfs = []

    with zipfile.ZipFile(zip_file, "r") as z:
        excel_files = [f for f in z.namelist() if f.endswith(".xlsx") and not f.startswith("~") and not f.startswith(".")]
        # Sort files chronologically by month
        month_order = ["january", "february", "march", "april", "may", "june"]
        def get_month_idx(filename: str) -> int:
            fn_lower = filename.lower()
            for i, m in enumerate(month_order):
                if m in fn_lower:
                    return i
            return 99
        excel_files.sort(key=get_month_idx)

        print(f"\nFound {len(excel_files)} monthly DPR workbooks inside ZIP:")
        for fn in excel_files:
            print(f"  • Processing: {fn} ...")
            file_bytes = z.read(fn)
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)

            if "DPR Report" not in wb.sheetnames:
                print(f"    [WARN] 'DPR Report' sheet missing in {fn}, skipping.")
                continue

            # Read raw sheet as 2D array
            df_raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name="DPR Report", header=None)
            if df_raw.empty or df_raw.shape[0] < 5:
                continue

            # Step 1: Dynamic Date Header Detection (Find row where col 0 is 'Date')
            date_row_idx = None
            for idx in range(min(20, len(df_raw))):
                val_0 = str(df_raw.iloc[idx, 0]).strip().lower()
                if val_0 == "date":
                    date_row_idx = idx
                    break

            if date_row_idx is None:
                # Fallback: find row containing 'date' in col 0 or col 1
                for idx in range(min(20, len(df_raw))):
                    val_0 = str(df_raw.iloc[idx, 0]).strip().lower()
                    val_1 = str(df_raw.iloc[idx, 1]).strip().lower()
                    if val_0 == "date" or val_1 == "date":
                        date_row_idx = idx
                        break

            if date_row_idx is None:
                print(f"    [WARN] Could not find 'Date' header row in {fn}, skipping.")
                continue

            # Step 2: Multi-Level Header Flattening (Rows date_row_idx to date_row_idx + 2)
            header_end = min(date_row_idx + 3, len(df_raw))
            headers_block = df_raw.iloc[date_row_idx:header_end].ffill(axis=1).fillna("")

            flattened_cols = []
            seen = {}
            for col_i in range(df_raw.shape[1]):
                col_parts = [str(headers_block.iloc[r, col_i]).strip() for r in range(len(headers_block))]
                clean_parts = []
                for p in col_parts:
                    p_clean = re.sub(r"\s+", " ", p).strip()
                    if p_clean and not p_clean.startswith("Unnamed") and p_clean not in clean_parts:
                        clean_parts.append(p_clean)

                base_name = " ".join(clean_parts) if clean_parts else f"col_{col_i}"
                # Handle duplicates
                if base_name in seen:
                    seen[base_name] += 1
                    col_name = f"{base_name}_{seen[base_name]}"
                else:
                    seen[base_name] = 0
                    col_name = base_name
                flattened_cols.append(col_name)

            # Step 3: Data Extraction & Footer Filtering
            df_data = df_raw.iloc[header_end:].copy()
            df_data.columns = flattened_cols

            # Keep only valid date rows (first column must contain valid date)
            valid_rows = []
            for r_i in range(len(df_data)):
                first_val = str(df_data.iloc[r_i, 0]).strip()
                if first_val and not any(k in first_val.lower() for k in ("total", "average", "mean", "min", "max", "#div", "nan", "none")):
                    if re.search(r"\d{4}-\d{2}-\d{2}", first_val) or re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", first_val):
                        valid_rows.append(df_data.iloc[r_i])

            if not valid_rows:
                # Fallback: keep rows where first col is a timestamp or date string
                for r_i in range(len(df_data)):
                    first_val = str(df_data.iloc[r_i, 0]).strip()
                    if first_val and first_val.lower() not in ("nan", "none", "") and not any(k in first_val.lower() for k in ("total", "average", "mean", "#div")):
                        valid_rows.append(df_data.iloc[r_i])

            if not valid_rows:
                continue

            df_clean = pd.DataFrame(valid_rows).reset_index(drop=True)

            # Step 4: Add Provenance Metadata
            df_clean.insert(0, "unit_id", "PNB950657")
            df_clean.insert(1, "source_file", fn)
            df_clean.insert(2, "sheet_name", "DPR Report")

            compiled_dfs.append(df_clean)
            print(f"    [OK] Extracted {len(df_clean)} daily operational rows × {len(flattened_cols)} parameters.")

    if not compiled_dfs:
        raise RuntimeError("No valid DPR Report data extracted from archive.")

    # Step 5: Assembly & Chronological Alignment
    # Standardize column headers across all monthly DataFrames
    base_cols = compiled_dfs[0].columns.tolist()

    aligned_dfs = []
    for df in compiled_dfs:
        # Match columns by length if identical shape
        if len(df.columns) == len(base_cols):
            df.columns = base_cols
        aligned_dfs.append(df)

    df_final = pd.concat(aligned_dfs, ignore_index=True)

    # Parse primary Date column
    date_col = "Date" if "Date" in df_final.columns else df_final.columns[3]
    df_final[date_col] = pd.to_datetime(df_final[date_col], errors="coerce")
    df_final = df_final.dropna(subset=[date_col]).sort_values(by=date_col).drop_duplicates(subset=[date_col]).reset_index(drop=True)

    output_csv = out_dir / "dataset_tas_dpr_compiled.csv"
    df_final.to_csv(output_csv, index=False)

    print(f"\n=== Compilation Complete ===")
    print(f"Output File  : {output_csv}")
    print(f"Total Rows   : {len(df_final)} Continuous Daily Operational Records")
    print(f"Total Cols   : {len(df_final.columns)} Parameters")
    print(f"Date Range   : {df_final[date_col].min().strftime('%Y-%m-%d')} to {df_final[date_col].max().strftime('%Y-%m-%d')}")

    return output_csv


if __name__ == "__main__":
    compile_dataset_tas()
