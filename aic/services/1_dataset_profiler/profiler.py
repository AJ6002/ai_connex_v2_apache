import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Column names that indicate a temporal/time-step dimension (even as float64 Unix epochs)
_TEMPORAL_NAMES = {'time', 'timestamp', 'date', 'datetime', 'cycle', 'cycles', 'step',
                   't', 'sec', 'second', 'seconds', 'elapsed', 'epoch', 'ts'}


def _is_numeric_temporal(series: pd.Series) -> bool:
    """
    Return True when a float/int column is very likely a time axis:
      - Column name is in _TEMPORAL_NAMES, OR
      - Column is strictly monotonically increasing (common for Unix-epoch runs).
    """
    col_name_lower = str(series.name).lower().strip()
    if col_name_lower in _TEMPORAL_NAMES:
        return True
    # Strictly monotonic check on a sample for speed
    if pd.api.types.is_numeric_dtype(series):
        sample = series.dropna().head(500)
        if len(sample) > 10 and sample.is_monotonic_increasing and sample.nunique() == len(sample):
            return True
    return False


def detect_column_type(series: pd.Series) -> str:
    """
    Detect the semantic type of a column.
    Possible values: 'id', 'numeric', 'categorical', 'datetime', 'text'
    """
    # 1. Check if it's a native datetime dtype
    if pd.api.types.is_datetime64_any_dtype(series):
        return 'datetime'

    # 2. Check numeric columns that represent a time axis (float Unix epoch, integer cycle index)
    if pd.api.types.is_numeric_dtype(series):
        if _is_numeric_temporal(series):
            return 'datetime'

    # 3. Try parsing string columns as datetime if they look like it
    if series.dtype == 'object' or isinstance(series.dtype, pd.StringDtype):
        sample = series.dropna().head(100)
        if len(sample) > 0:
            try:
                parsed = pd.to_datetime(sample, errors='coerce')
                if parsed.notna().sum() / len(sample) > 0.8:
                    return 'datetime'
            except Exception:
                pass

    # 4. Check if it's an ID column
    col_name_lower = str(series.name).lower()
    is_id_name = any(x in col_name_lower for x in ['id', 'key', 'uuid', 'guid', 'code', 'pk', 'fk'])
    non_null_count = series.count()
    if non_null_count > 0:
        unique_ratio = series.nunique() / non_null_count
        if (is_id_name and unique_ratio > 0.9) or (unique_ratio == 1.0 and pd.api.types.is_integer_dtype(series)):
            return 'id'

    # 5. Check if numeric
    if pd.api.types.is_numeric_dtype(series):
        if series.nunique() <= 2 and set(series.dropna().unique()).issubset({0, 1, 0.0, 1.0, True, False}):
            return 'categorical'
        return 'numeric'

    # 6. Check if text or categorical
    if series.dtype == 'object' or isinstance(series.dtype, pd.StringDtype) or isinstance(series.dtype, pd.CategoricalDtype):
        non_null_vals = series.dropna()
        if len(non_null_vals) == 0:
            return 'categorical'
        avg_len = non_null_vals.astype(str).str.len().mean()
        unique_ratio = series.nunique() / len(non_null_vals) if len(non_null_vals) > 0 else 0
        if avg_len > 35 and unique_ratio > 0.5:
            return 'text'
        return 'categorical'

    return 'categorical'

def calculate_numeric_stats(series: pd.Series) -> dict:
    """Calculate statistics for numeric columns."""
    stats = {}
    non_null_series = series.dropna()
    
    if len(non_null_series) == 0:
        return stats
        
    stats['min'] = float(non_null_series.min())
    stats['max'] = float(non_null_series.max())
    stats['mean'] = float(non_null_series.mean())
    stats['median'] = float(non_null_series.median())
    stats['std'] = float(non_null_series.std()) if len(non_null_series) > 1 else 0.0
    stats['variance'] = float(non_null_series.var()) if len(non_null_series) > 1 else 0.0
    
    # Skewness and kurtosis
    stats['skewness'] = float(non_null_series.skew()) if len(non_null_series) > 2 else 0.0
    stats['kurtosis'] = float(non_null_series.kurt()) if len(non_null_series) > 3 else 0.0
    
    # Percentiles
    percentiles = [0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
    perc_vals = non_null_series.quantile(percentiles)
    stats['percentiles'] = {f"{int(p*100)}%": float(v) for p, v in zip(percentiles, perc_vals)}
    
    # Outliers
    # 1. IQR method
    q25 = stats['percentiles']['25%']
    q75 = stats['percentiles']['75%']
    iqr = q75 - q25
    if iqr > 0:
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr
        outliers_iqr = non_null_series[(non_null_series < lower_bound) | (non_null_series > upper_bound)]
        stats['outlier_count_iqr'] = int(len(outliers_iqr))
        stats['outlier_pct_iqr'] = float(len(outliers_iqr) / len(series))
    else:
        stats['outlier_count_iqr'] = 0
        stats['outlier_pct_iqr'] = 0.0
        
    # 2. Z-score method (threshold = 3)
    if stats['std'] > 0:
        z_scores = (non_null_series - stats['mean']) / stats['std']
        outliers_z = non_null_series[z_scores.abs() > 3]
        stats['outlier_count_zscore'] = int(len(outliers_z))
        stats['outlier_pct_zscore'] = float(len(outliers_z) / len(series))
    else:
        stats['outlier_count_zscore'] = 0
        stats['outlier_pct_zscore'] = 0.0

    # Histogram
    try:
        counts, bin_edges = np.histogram(non_null_series, bins=10)
        stats['histogram'] = {
            'counts': counts.tolist(),
            'bin_edges': bin_edges.tolist()
        }
    except Exception:
        stats['histogram'] = None
        
    return stats

def calculate_categorical_stats(series: pd.Series) -> dict:
    """Calculate statistics for categorical columns."""
    stats = {}
    non_null_series = series.dropna()
    
    if len(non_null_series) == 0:
        return stats
        
    # Top values
    vc = non_null_series.value_counts()
    top_n = vc.head(15)
    stats['top_categories'] = {str(k): int(v) for k, v in top_n.to_dict().items()}
    
    stats['mode'] = str(vc.index[0]) if len(vc) > 0 else None
    stats['mode_frequency'] = int(vc.iloc[0]) if len(vc) > 0 else 0
    stats['mode_pct'] = float(vc.iloc[0] / len(series)) if len(vc) > 0 else 0.0
    
    # Calculate Shannon Entropy
    probs = vc / len(non_null_series)
    stats['entropy'] = float(entropy(probs))
    
    return stats

def calculate_datetime_stats(series: pd.Series) -> dict:
    """Calculate statistics for datetime columns."""
    stats = {}
    # Make sure it's datetime
    dt_series = pd.to_datetime(series, errors='coerce')
    non_null_series = dt_series.dropna()
    
    if len(non_null_series) == 0:
        return stats
        
    stats['min'] = str(non_null_series.min())
    stats['max'] = str(non_null_series.max())
    stats['range_days'] = float((non_null_series.max() - non_null_series.min()).days)
    
    return stats

def calculate_text_stats(series: pd.Series) -> dict:
    """Calculate statistics for text columns."""
    stats = {}
    non_null_series = series.dropna().astype(str)
    
    if len(non_null_series) == 0:
        return stats
        
    lens = non_null_series.str.len()
    stats['min_length'] = int(lens.min())
    stats['max_length'] = int(lens.max())
    stats['mean_length'] = float(lens.mean())
    
    # Word count stats
    word_counts = non_null_series.str.split().str.len()
    stats['mean_word_count'] = float(word_counts.mean())
    stats['max_word_count'] = int(word_counts.max())
    
    return stats

def generate_profile(df: pd.DataFrame) -> dict:
    """Generate the full dataset profile dictionary."""
    num_rows = len(df)
    num_columns = len(df.columns)
    
    profile = {
        "dataset_info": {
            "num_rows": num_rows,
            "num_columns": num_columns,
            "total_memory_bytes": int(df.memory_usage(deep=True).sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "duplicate_rows_pct": float(df.duplicated().sum() / num_rows) if num_rows > 0 else 0.0
        },
        "columns": [],
        "correlation_summary": {
            "warnings": []
        },
        "missing_data_summary": {
            "total_missing_cells": int(df.isna().sum().sum()),
            "overall_missing_pct": float(df.isna().sum().sum() / (num_rows * num_columns)) if num_rows > 0 and num_columns > 0 else 0.0,
            "columns_above_20pct_missing": []
        },
        "outlier_summary": {
            "overall_outlier_ratio": 0.0,
            "top_outlier_columns": []
        },
        "dimensionality": {
            "pca_95pct_components": 0,
            "components_needed_ratio": 0.0
        },
        "warnings": []
    }

    # Will be set to 'time_series' if a temporal column is detected
    profile['data_topology'] = 'tabular'

    if num_rows == 0:
        return profile
        
    # Profile columns
    numeric_cols = []
    outlier_pacts = {}
    
    for col in df.columns:
        series = df[col]
        col_type = detect_column_type(series)
        
        missing_count = int(series.isna().sum())
        missing_pct = float(missing_count / num_rows)
        unique_count = int(series.nunique())
        unique_pct = float(unique_count / num_rows)
        
        col_profile = {
            "name": str(col),
            "dtype": str(series.dtype),
            "semantic_type": col_type,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "unique_count": unique_count,
            "unique_pct": unique_pct,
            "is_constant": unique_count <= 1
        }
        
        if col_type == 'numeric':
            numeric_cols.append(col)
            stats = calculate_numeric_stats(series)
            col_profile['stats'] = stats
            if 'outlier_pct_iqr' in stats:
                outlier_pacts[col] = stats['outlier_pct_iqr']
        elif col_type == 'categorical':
            col_profile['stats'] = calculate_categorical_stats(series)
        elif col_type == 'datetime':
            col_profile['stats'] = calculate_datetime_stats(series)
        elif col_type == 'text':
            col_profile['stats'] = calculate_text_stats(series)
            
        profile['columns'].append(col_profile)

        # Tag data topology when a temporal column is found
        if col_type == 'datetime':
            profile['data_topology'] = 'time_series'

        # Warnings checks
        if col_profile['is_constant']:
            profile['warnings'].append(f"Column '{col}' is constant (only has 1 unique value) and has no predictive power.")
        if missing_pct > 0.2:
            profile['missing_data_summary']['columns_above_20pct_missing'].append(str(col))
            profile['warnings'].append(f"Column '{col}' has a high percentage of missing values ({missing_pct:.1%}).")
        if col_type == 'id':
            profile['warnings'].append(f"Column '{col}' is classified as an Identifier (ID/Key). It should not be used as an input feature.")

    # Duplicate rows warning
    if profile['dataset_info']['duplicate_rows'] > 0:
        profile['warnings'].append(f"Dataset has {profile['dataset_info']['duplicate_rows']} duplicate rows.")

    # High Correlation detection
    if len(numeric_cols) > 1:
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr(method='pearson')
        # Find pairs
        high_corr_pairs = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                col1 = numeric_cols[i]
                col2 = numeric_cols[j]
                val = corr_matrix.loc[col1, col2]
                if abs(val) > 0.85:
                    high_corr_pairs.append({
                        "col1": str(col1),
                        "col2": str(col2),
                        "correlation": float(val)
                    })
                    profile['correlation_summary']['warnings'].append(
                        f"High correlation between '{col1}' and '{col2}' ({val:.2f}). One could be redundant."
                    )
        profile['correlation_summary']['high_correlation_pairs'] = high_corr_pairs
    else:
        profile['correlation_summary']['high_correlation_pairs'] = []

    # Outlier summaries
    if outlier_pacts:
        profile['outlier_summary']['overall_outlier_ratio'] = float(np.mean(list(outlier_pacts.values())))
        # Sort outlier columns descending
        sorted_outliers = sorted(outlier_pacts.items(), key=lambda x: x[1], reverse=True)
        profile['outlier_summary']['top_outlier_columns'] = [
            {"column": str(col), "outlier_ratio": float(pct)} for col, pct in sorted_outliers if pct > 0
        ]
        
        # Add warnings for high outliers
        for col, pct in sorted_outliers:
            if pct > 0.08:
                profile['warnings'].append(f"Column '{col}' has a high percentage of outliers ({pct:.1%}).")

    # Dimensionality & PCA (using numeric columns)
    if len(numeric_cols) >= 2:
        try:
            # Impute numeric columns with median, scale, and run PCA
            num_data = df[numeric_cols].copy()
            # simple fillna
            for col in numeric_cols:
                num_data[col] = num_data[col].fillna(num_data[col].median() if num_data[col].notna().any() else 0)
                
            # If standard dev of a col is 0, StandardScaler will fail, so drop constant columns
            num_data = num_data.loc[:, num_data.std() > 0]
            
            if num_data.shape[1] >= 2:
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(num_data)
                
                pca = PCA()
                pca.fit(scaled_data)
                
                # Cumulative variance
                cum_var = np.cumsum(pca.explained_variance_ratio_)
                # components explaining 95%
                components_95 = int(np.argmax(cum_var >= 0.95) + 1)
                
                profile['dimensionality']['pca_95pct_components'] = components_95
                profile['dimensionality']['components_needed_ratio'] = float(components_95 / num_data.shape[1])
                profile['dimensionality']['explained_variance_ratio'] = pca.explained_variance_ratio_.tolist()
                
                # Check for redundancy
                if profile['dimensionality']['components_needed_ratio'] < 0.4:
                    profile['warnings'].append(
                        f"High dimensionality redundancy. 95% variance explained by just {components_95} "
                        f"out of {num_data.shape[1]} numeric columns ({profile['dimensionality']['components_needed_ratio']:.1%} of columns)."
                    )
        except Exception as e:
            # PCA failed
            profile['dimensionality']['error'] = str(e)
            
    return profile
