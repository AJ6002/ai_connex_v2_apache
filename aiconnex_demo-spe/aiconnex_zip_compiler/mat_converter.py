"""
mat_converter.py — MATLAB (.mat) File Auto-Converter for aiconnex_zip_compiler
================================================================================
Detects and converts MATLAB (.mat) data structures (e.g. cycle-based battery or sensor structs)
into clean, tabular pandas DataFrames / CSV files during discovery.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
import scipy.io


def convert_mat_file_to_csv(mat_path: Path) -> Optional[Path]:
    """
    Parses a MATLAB .mat file and extracts tabular structs (like cycle-based sensor measurements).
    Saves the extracted table as a sibling .csv file and returns its path.
    """
    try:
        mat = scipy.io.loadmat(mat_path)
        var_keys = [k for k in mat.keys() if not k.startswith("__")]
        
        if not var_keys:
            return None

        records = []
        for key in var_keys:
            obj = mat[key]
            
            # Struct array case (e.g., Battery B0005 struct with 'cycle' field)
            if hasattr(obj, 'dtype') and obj.dtype.names and 'cycle' in obj.dtype.names:
                struct = obj[0, 0]
                cycles = struct['cycle'][0]
                
                discharge_idx = 0
                for c_idx, cycle in enumerate(cycles):
                    c_type = cycle['type'][0] if 'type' in cycle.dtype.names else 'unknown'
                    
                    if 'data' in cycle.dtype.names:
                        data = cycle['data'][0, 0]
                        v_measured = data['Voltage_measured'][0] if 'Voltage_measured' in data.dtype.names else np.array([])
                        i_measured = data['Current_measured'][0] if 'Current_measured' in data.dtype.names else np.array([])
                        t_measured = data['Temperature_measured'][0] if 'Temperature_measured' in data.dtype.names else np.array([])
                        time_seq = data['Time'][0] if 'Time' in data.dtype.names else np.array([])
                        
                        cap = float(data['Capacity'][0][0]) if 'Capacity' in data.dtype.names and len(data['Capacity']) > 0 else np.nan
                        
                        if len(v_measured) > 0:
                            discharge_idx += 1
                            rec = {
                                "asset_id": mat_path.stem,
                                "cycle_id": discharge_idx,
                                "type": str(c_type),
                                "capacity_ahr": cap,
                                "v_mean": float(np.mean(v_measured)),
                                "v_min": float(np.min(v_measured)),
                                "v_max": float(np.max(v_measured)),
                                "v_std": float(np.std(v_measured)),
                                "i_mean": float(np.mean(i_measured)),
                                "t_mean": float(np.mean(t_measured)),
                                "t_max": float(np.max(t_measured)),
                                "duration_sec": float(time_seq[-1] - time_seq[0]) if len(time_seq) > 1 else 0.0,
                            }
                            records.append(rec)

        if records:
            df = pd.DataFrame(records)
            # Synthesize RUL countdown target
            if "capacity_ahr" in df.columns:
                df_dis = df.dropna(subset=["capacity_ahr"]).copy()
                total_n = len(df_dis)
                df_dis["RUL"] = [total_n - (i + 1) for i in range(total_n)]
                df = df_dis
                
            csv_path = mat_path.with_suffix(".csv")
            df.to_csv(csv_path, index=False)
            return csv_path

    except Exception:
        pass

    return None
