import pandas as pd
import re
import os
import json

def detect_family(df: pd.DataFrame, profile: dict, target_hint: str = None) -> dict:
    """
    Detect the algorithm family of a dataset.
    Returns:
        {
            "algorithm_family": str ("Regression" | "Anomaly Detection" | "Miscellaneous"),
            "family_confidence": float (0.0 to 1.0),
            "reason": str,
            "target_column": str | None,
            "suggested_task": str ("Regression" | "Classification" | "Anomaly Detection" | "Clustering" | "Time Series Analysis" | "Dimensionality Reduction" | "Unknown")
        }
    """
    num_rows = profile['dataset_info']['num_rows']
    num_columns = profile['dataset_info']['num_columns']
    
    if num_rows == 0 or num_columns == 0:
        return {
            "algorithm_family": "Miscellaneous",
            "family_confidence": 1.0,
            "reason": "Empty dataset.",
            "target_column": None,
            "suggested_task": "Unknown"
        }

    # 1. Try to identify the target column
    target_column = None
    
    # Check if hint is valid
    if target_hint and target_hint in df.columns:
        target_column = target_hint
    else:
        # Heuristic search — anchored exact patterns (highest confidence matches)
        target_keywords_exact = [
            r'^target$', r'^label$', r'^y$', r'^class$', r'^output$', r'^response$',
            r'^result$', r'^price$', r'^revenue$', r'^income$', r'^pred$', r'^predict$',
            r'^outcome$', r'^diagnose$', r'^churn$', r'^sold$', r'^expensive$', r'^val$', r'^value$',
            r'^faulty$', r'^fault$', r'^status$', r'^fail$', r'^flag$', r'^rul$', r'^health_index$'
        ]
        # Substring/partial patterns (industrial sensor & physics targets) — use re.search
        target_keywords_partial = [
            'collector_current', 'collector_voltage', 'gate_current', 'gate_voltage',
            'package_temp', 'heat_sink_temp', 'package_temperture',
            'temperature', 'temp', 'current', 'voltage', 'power', 'energy',
            'pressure', 'vibration', 'rpm', 'speed', 'torque', 'load', 'stress',
            'degradation', 'wear', 'erosion', 'health', 'condition', 'anomaly_score',
            'failure', 'remaining_life', 'remaining_useful', 'survival'
        ]

        # Priority 1: Anchored exact matches
        for col in df.columns:
            col_lower = str(col).lower()
            for pattern in target_keywords_exact:
                if re.match(pattern, col_lower):
                    if not (col_lower.endswith('id') or col_lower.endswith('key')):
                        target_column = col
                        break
            if target_column:
                break

        # Priority 2: Partial substring match on column names (industrial sensors)
        if not target_column:
            for col in df.columns:
                col_lower = str(col).lower()
                if col_lower.endswith('id') or col_lower.endswith('key'):
                    continue
                for partial in target_keywords_partial:
                    if re.search(partial, col_lower):
                        # Confirm it's a numeric column with good variance
                        col_profile = next((c for c in profile.get('columns', []) if c['name'] == col), None)
                        if col_profile and col_profile['semantic_type'] == 'numeric' and not col_profile['is_constant']:
                            target_column = col
                            break
                if target_column:
                    break

        # Priority 3: If no target found, check if last column looks like a target
        if not target_column and len(df.columns) > 1:
            last_col = df.columns[-1]
            last_col_lower = str(last_col).lower()
            last_col_profile = next((c for c in profile['columns'] if c['name'] == last_col), None)
            if last_col_profile and last_col_profile['semantic_type'] in ['numeric', 'categorical'] and not last_col_profile['is_constant']:
                target_like_words = ['target', 'label', 'class', 'churn', 'price', 'revenue', 'income',
                                     'pred', 'predict', 'outcome', 'diagnose', 'sold', 'expensive',
                                     'val', 'value', 'y', 'output', 'response', 'result', 'status', 'fail', 'flag']
                if any(w in last_col_lower for w in target_like_words):
                    if 'id' not in last_col_lower and 'key' not in last_col_lower:
                        target_column = last_col

    # 2. Evaluate target column if present
    if target_column:
        target_profile = next((c for c in profile['columns'] if c['name'] == target_column), None)

        if target_profile:
            unique_count = target_profile['unique_count']
            semantic_type = target_profile['semantic_type']
            data_topology = profile.get('data_topology', 'tabular')

            # Continuous numeric target -> Time Series Regression or plain Regression
            if semantic_type == 'numeric' and unique_count > 20:
                unique_pct = target_profile['unique_pct']
                if data_topology == 'time_series':
                    return {
                        "algorithm_family": "Regression",
                        "family_confidence": round(min(0.88 + (unique_pct * 0.1), 0.98), 2),
                        "reason": f"Temporal column detected + continuous numeric target '{target_column}' "
                                  f"({unique_count} unique values). Routes to Time Series Regression.",
                        "target_column": target_column,
                        "suggested_task": "Time Series Analysis"
                    }
                return {
                    "algorithm_family": "Regression",
                    "family_confidence": round(min(0.85 + (unique_pct * 0.1), 0.98), 2),
                    "reason": f"Identified numeric target column '{target_column}' with high cardinality ({unique_count} unique values), which strongly indicates a Regression task.",
                    "target_column": target_column,
                    "suggested_task": "Regression"
                }

            # Categorical or low-cardinality target -> Classification
            else:
                task = "Classification"
                reason = f"Identified target column '{target_column}' which is categorical or has low cardinality ({unique_count} unique values), indicating a Classification task."
                if unique_count == 2:
                    task = "Classification (Binary)"
                return {
                    "algorithm_family": "Miscellaneous",
                    "family_confidence": 0.90,
                    "reason": reason,
                    "target_column": target_column,
                    "suggested_task": task
                }

    # 3. Early time-series gate — evaluated BEFORE anomaly scoring
    #    Prevents high-outlier time-series telemetry from being swallowed by Anomaly Detection.
    data_topology = profile.get('data_topology', 'tabular')
    numeric_cols = [c for c in profile['columns'] if c['semantic_type'] == 'numeric']
    datetime_cols = [c for c in profile['columns'] if c['semantic_type'] == 'datetime']

    if data_topology == 'time_series' and len(numeric_cols) > 0:
        return {
            "algorithm_family": "Anomaly Detection",
            "family_confidence": 0.82,
            "reason": "Temporal column detected without explicit target — routes to Anomaly Detection for "
                      "unsupervised health-index scoring on continuous sensor telemetry.",
            "target_column": None,
            "suggested_task": "Anomaly Detection"
        }

    # 4. If no target column is detected, check if it's suited for Anomaly Detection
    numeric_cols = [c for c in profile['columns'] if c['semantic_type'] == 'numeric']
    datetime_cols = [c for c in profile['columns'] if c['semantic_type'] == 'datetime']
    
    anomaly_score = 0.3  # Base score
    reasons = []
    
    overall_outlier_ratio = profile['outlier_summary']['overall_outlier_ratio']
    if len(numeric_cols) > 0:
        if overall_outlier_ratio > 0.05:
            anomaly_score += 0.25
            reasons.append(f"high overall outlier ratio ({overall_outlier_ratio:.1%}) across numeric features")
        elif overall_outlier_ratio > 0.02:
            anomaly_score += 0.1
            reasons.append(f"moderate outlier presence ({overall_outlier_ratio:.1%})")
            
        skews = [abs(c['stats']['skewness']) for c in numeric_cols if 'stats' in c and 'skewness' in c['stats']]
        if skews:
            mean_skew = sum(skews) / len(skews)
            if mean_skew > 1.8:
                anomaly_score += 0.2
                reasons.append(f"highly skewed features (avg absolute skewness of {mean_skew:.2f})")
            elif mean_skew > 1.0:
                anomaly_score += 0.1
                reasons.append(f"moderately skewed features (avg absolute skewness of {mean_skew:.2f})")
                
        high_outlier_cols = [c for c in profile['outlier_summary']['top_outlier_columns'] if c['outlier_ratio'] > 0.08]
        if len(high_outlier_cols) >= 2:
            anomaly_score += 0.15
            reasons.append(f"{len(high_outlier_cols)} columns with substantial outlier percentages (>8%)")

    if datetime_cols:
        anomaly_score += 0.1
        reasons.append("presence of a temporal/datetime column")

    # Cap anomaly score
    anomaly_score = min(anomaly_score, 0.95)
    
    if anomaly_score >= 0.6 and len(numeric_cols) > 0:
        reason_str = "No target column detected. Suitability for Anomaly Detection is high based on: " + ", ".join(reasons) + "."
        return {
            "algorithm_family": "Anomaly Detection",
            "family_confidence": round(anomaly_score, 2),
            "reason": reason_str,
            "target_column": None,
            "suggested_task": "Anomaly Detection"
        }

    # 5. Fallback to Miscellaneous
    misc_reasons = ["No target column detected for supervised learning (Regression/Classification)"]
    if len(numeric_cols) == 0:
        misc_reasons.append("no numeric columns found in the dataset")
    if data_topology == 'time_series' or datetime_cols:
        suggested = "Time Series Analysis"
        misc_reasons.append("has a temporal component, indicating time-series or sequence analysis")
    elif len(numeric_cols) > 5 and len(numeric_cols) / num_columns > 0.8:
        suggested = "Clustering"
        misc_reasons.append("high-dimensional numeric features without obvious anomalies, ideal for unsupervised clustering")
    else:
        suggested = "Clustering / Association Rules"
        misc_reasons.append("mixed categorical/numeric columns without label, suggesting clustering or rule association")

    reason_str = "; ".join(misc_reasons) + "."
    return {
        "algorithm_family": "Miscellaneous",
        "family_confidence": 0.80,
        "reason": reason_str,
        "target_column": None,
        "suggested_task": suggested
    }

def decide_dag_and_details(df: pd.DataFrame, profile: dict, family_result: dict) -> dict:
    """
    Decides the recommended DAG ID, algorithm, variant, and special handling parameters
    from the list of 1690 DAG IDs based on profiled dataset characteristics.
    """
    base_path = os.path.dirname(__file__)
    mapping_path = os.path.join(base_path, "dag_mapping.json")
    
    mapping_db = {}
    if os.path.exists(mapping_path):
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping_db = json.load(f)
        except Exception as e:
            print("Failed to load dag_mapping.json:", e)
            
    family = family_result.get("algorithm_family", "Miscellaneous")
    task = family_result.get("suggested_task", "Clustering")
    
    # Standard fallback defaults
    rec_dag_id = "DAG_001"
    rec_algo = "AdaBoost"
    rec_variant = "Standard"
    rec_special = "None"
    
    # 1. Resolve target family key in the JSON mapping
    family_key = None
    if family == "Regression":
        family_key = "REGRESSION"
    elif family == "Anomaly Detection":
        family_key = "ANOMALY DETECTION"
    elif family == "Miscellaneous":
        if "Classification" in task:
            family_key = "CLASSIFICATION"
        elif "Clustering" in task:
            family_key = "CLUSTERING"
        elif "Time Series" in task:
            family_key = "TIME-SERIES"
        else:
            family_key = "CLASSIFICATION"
            
    # Additional checks for specialized families (only apply if not explicitly REGRESSION or ANOMALY DETECTION)
    if family not in ("Regression", "Anomaly Detection"):
        if "time" in str(task).lower():
            family_key = "TIME-SERIES"
        elif "twin" in str(task).lower():
            family_key = "DIGITAL TWIN"
        elif "reinforcement" in str(task).lower():
            family_key = "REINFORCEMENT LEARNING"
        elif "recommend" in str(task).lower():
            family_key = "RECOMMENDATION"
        elif "nlp" in str(task).lower() or "text" in str(task).lower():
            family_key = "NLP/TEXT-CLASSIFICATION"
        elif "vision" in str(task).lower() or "image" in str(task).lower():
            family_key = "COMPUTER VISION"
        
    family_rows = mapping_db.get(family_key or "CLASSIFICATION", [])
    
    # 2. Match algorithm and variant by checking dataset properties
    target_algo = "AdaBoost"
    target_variant = "Standard"
    
    num_rows = profile['dataset_info']['num_rows']
    outlier_pct = profile['outlier_summary']['overall_outlier_ratio']
    
    # Collinearity check
    corr_pairs = profile.get('correlation_summary', {}).get('high_correlation_pairs', [])
    has_high_corr = len(corr_pairs) > 0
    
    # Text & datetime column presence
    has_text = any(c['semantic_type'] == 'text' for c in profile.get('columns', []))
    has_date = any(c['semantic_type'] == 'datetime' for c in profile.get('columns', []))
    
    if family_key == "CLASSIFICATION":
        if num_rows > 10000:
            target_algo = "LightGBM"
            target_variant = "Standard"
        elif has_high_corr:
            target_algo = "Logistic Regression"
            target_variant = "L1 Regularization"
        elif outlier_pct > 0.05:
            target_algo = "Random Forest"
            target_variant = "Weighted"
        elif has_text:
            target_algo = "Naïve Bayes"
            target_variant = "Multinomial"
        else:
            target_algo = "XGBoost"
            target_variant = "Standard"
            
    elif family_key == "REGRESSION":
        if num_rows > 10000 or has_date:
            target_algo = "LightGBM"
            target_variant = "Standard"
        elif outlier_pct > 0.05:
            target_algo = "Gradient Boosting"
            target_variant = "Standard"
        elif has_high_corr:
            target_algo = "Ridge Regression"
            target_variant = "Standard"
        else:
            target_algo = "XGBoost"
            target_variant = "Standard"
            
    elif family_key == "ANOMALY DETECTION":
        target_algo = "Isolation Forest"
        target_variant = "Standard"
            
    elif family_key == "CLUSTERING":
        target_algo = "K-Means"
        target_variant = "Standard"
            
    elif family_key == "TIME-SERIES":
        numeric_count = sum(1 for c in profile.get('columns', []) if c['semantic_type'] == 'numeric')
        if numeric_count > 2:
            target_algo = "XGBoost"
            target_variant = "Standard"
        else:
            target_algo = "ARIMA"
            target_variant = "Standard"
    elif family_key == "DIGITAL TWIN":
        target_algo = "Surrogate Neural Network"
        target_variant = "Standard"
    elif family_key == "REINFORCEMENT LEARNING":
        target_algo = "PPO"
        target_variant = "Standard"
    elif family_key == "RECOMMENDATION":
        target_algo = "Collaborative Filtering"
        target_variant = "Standard"
    elif family_key == "NLP/TEXT-CLASSIFICATION":
        target_algo = "BERT Classifier"
        target_variant = "Standard"
    elif family_key == "COMPUTER VISION":
        target_algo = "CNN Classifier"
        target_variant = "Standard"
        
    # Search for matching algorithm & variant in JSON dataset
    matched_row = None
    for row in family_rows:
        algo_name = row["algorithm"].lower()
        var_name = row["variant"].lower()
        
        # Soft match
        if target_algo.lower() in algo_name and target_variant.lower() in var_name:
            matched_row = row
            break
            
    # Default to first row of family if no soft match found
    if not matched_row and family_rows:
        matched_row = family_rows[0]
        
    if matched_row:
        rec_dag_id = matched_row.get("dag_id", matched_row.get("DAG ID", "DAG_001"))
        rec_algo = matched_row.get("algorithm", matched_row.get("Algorithm", "Random Forest"))
        rec_variant = matched_row.get("variant", matched_row.get("Variant", "Standard"))
        rec_special = matched_row.get("special_handling", matched_row.get("Special Handling", "None"))
        
    return {
        "recommended_dag_id": rec_dag_id,
        "recommended_algorithm": rec_algo,
        "recommended_variant": rec_variant,
        "recommended_special_handling": rec_special
    }
