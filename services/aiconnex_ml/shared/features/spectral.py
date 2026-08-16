"""
spectral.py — FFT and wavelet features for vibration/acoustic sensor data
=========================================================================
Used when manifest["features_config"]["spectral_features"] = true.
Extracts frequency-domain features from time-domain sensor signals.
"""

from __future__ import annotations
from typing import List
import numpy as np
import pandas as pd


def add_fft_features(
    df: pd.DataFrame,
    cols: List[str],
    window: int = 256,
    n_components: int = 10,
    group_col: str | None = None,
) -> pd.DataFrame:
    """
    Compute rolling FFT magnitude features for vibration sensor columns.
    Extracts the top-N frequency components' amplitudes.

    Args:
        df:           Input DataFrame.
        cols:         Sensor columns (e.g., vibration, acoustic).
        window:       Number of samples per FFT window.
        n_components: Number of frequency components to extract.
        group_col:    Compute FFT per entity group.

    Returns:
        DataFrame with FFT amplitude features appended.
    """
    df = df.copy()

    def compute_rolling_fft(series: pd.Series) -> pd.DataFrame:
        results = []
        values = series.values
        for i in range(len(values)):
            start = max(0, i - window + 1)
            segment = values[start:i + 1]
            if len(segment) < 4:
                results.append([0.0] * n_components)
                continue
            fft_magnitudes = np.abs(np.fft.rfft(segment))
            # Take top N components (excluding DC component at index 0)
            top_n = fft_magnitudes[1:n_components + 1]
            # Pad if segment is shorter than n_components
            if len(top_n) < n_components:
                top_n = np.pad(top_n, (0, n_components - len(top_n)))
            results.append(top_n.tolist())
        return pd.DataFrame(results, index=series.index,
                            columns=[f"fft_c{k+1}" for k in range(n_components)])

    for col in cols:
        if col not in df.columns:
            continue
        if group_col and group_col in df.columns:
            fft_parts = []
            for _, grp in df.groupby(group_col):
                fft_part = compute_rolling_fft(grp[col])
                fft_part.columns = [f"{col}_{c}" for c in fft_part.columns]
                fft_parts.append(fft_part)
            fft_df = pd.concat(fft_parts).sort_index()
        else:
            fft_df = compute_rolling_fft(df[col])
            fft_df.columns = [f"{col}_{c}" for c in fft_df.columns]

        df = pd.concat([df, fft_df], axis=1)

    print(f"[Spectral] FFT features added for: {cols}")
    return df


def add_statistical_spectral_features(
    df: pd.DataFrame,
    cols: List[str],
    window: int = 128,
) -> pd.DataFrame:
    """
    Add simpler spectral summary statistics (RMS, crest factor, kurtosis)
    for sensors without full FFT decomposition.
    These are computationally cheap and effective for detecting bearing faults.
    """
    df = df.copy()

    for col in cols:
        if col not in df.columns:
            continue
        roll = df[col].rolling(window, min_periods=1)
        df[f"{col}_rms"] = roll.apply(lambda x: float(np.sqrt(np.mean(x ** 2))), raw=True)
        df[f"{col}_kurtosis"] = roll.kurt()
        roll_max = roll.max()
        roll_rms = df[f"{col}_rms"]
        df[f"{col}_crest"] = roll_max / (roll_rms.replace(0, np.nan))

    print(f"[Spectral] Statistical spectral features added for: {cols}")
    return df
