import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DAG_CONDITIONS_PATH = os.path.join(os.path.dirname(BASE_DIR), "2_dag", "dag_conditions_mapping.json")

RECIPE_DIR = os.path.join(BASE_DIR, "recipe")
PREPARING_DIR = os.path.join(RECIPE_DIR, "preparing")
FEATURE_ENG_DIR = os.path.join(RECIPE_DIR, "feature_engineering")
SPLITTING_DIR = os.path.join(RECIPE_DIR, "splitting")
TRAINING_DIR = os.path.join(RECIPE_DIR, "training")

for d in [PREPARING_DIR, FEATURE_ENG_DIR, SPLITTING_DIR, TRAINING_DIR]:
    os.makedirs(d, exist_ok=True)

def get_metrics_for_family(family):
    fam = str(family).upper()
    if "REGRESSION" in fam:
        return ["r2", "rmse", "mae"]
    elif "ANOMALY" in fam:
        return ["f1", "precision", "recall", "auc_roc"]
    elif "CLUSTERING" in fam:
        return ["silhouette_score", "calinski_harabasz"]
    elif "TIME" in fam:
        return ["mape", "rmse", "mae"]
    elif "RECOMMEND" in fam:
        return ["ndcg", "precision_at_k", "recall_at_k"]
    elif "NLP" in fam or "VISION" in fam or "CLASSIF" in fam:
        return ["accuracy", "f1", "precision", "recall"]
    else:
        return ["accuracy", "f1"]

def get_hyperparameters(algo, variant):
    algo_str = str(algo).lower()
    var_str = str(variant).lower()
    
    if "logistic" in algo_str:
        return {"penalty": "l2", "C": 1.0, "solver": "lbfgs"}
    elif "random forest" in algo_str or "rf" in algo_str:
        return {"n_estimators": 100, "max_depth": 10, "min_samples_split": 2}
    elif "gradient boosting" in algo_str or "gbm" in algo_str or "xgboost" in algo_str:
        return {"n_estimators": 100, "learning_rate": 0.1, "max_depth": 5}
    elif "svm" in algo_str or "support vector" in algo_str:
        return {"C": 1.0, "kernel": "rbf", "gamma": "scale"}
    elif "linear regression" in algo_str or "ridge" in algo_str or "lasso" in algo_str:
        return {"fit_intercept": True, "alpha": 1.0}
    elif "k-means" in algo_str or "kmeans" in algo_str:
        return {"n_clusters": 3, "init": "k-means++"}
    elif "dbscan" in algo_str:
        return {"eps": 0.5, "min_samples": 5}
    elif "isolation" in algo_str:
        return {"n_estimators": 100, "contamination": 0.05}
    elif "arima" in algo_str or "sarima" in algo_str:
        return {"p": 1, "d": 1, "q": 1}
    elif "lstm" in algo_str or "gru" in algo_str:
        return {"units": 64, "epochs": 20, "batch_size": 32}
    else:
        return {"n_estimators": 50, "max_depth": 6}

def main():
    if not os.path.exists(DAG_CONDITIONS_PATH):
        print(f"Error: {DAG_CONDITIONS_PATH} not found.")
        return

    with open(DAG_CONDITIONS_PATH, "r", encoding="utf-8") as f:
        dag_conditions = json.load(f)

    count = 0
    for dag_id, item in dag_conditions.items():
        family = item.get("family", "CLASSIFICATION")
        algo = item.get("algorithm", "Estimator")
        variant = item.get("variant", "Standard")
        decision = item.get("decision", {})
        pa = decision.get("pipeline_actions", {})

        # 1. Preparing Recipe
        prep_rec = {
            "impute_strategy": pa.get("imputation", "mean"),
            "outlier_method": pa.get("outlier_handling", "none"),
            "scale_method": pa.get("scaling", "standard"),
            "encode_strategy": pa.get("encoding", "one-hot"),
            "text_clean": True if ("NLP" in str(family).upper() or "VISION" in str(family).upper()) else False,
            "time_align": True if ("TIME" in str(family).upper() or "TWIN" in str(family).upper()) else False
        }

        # 2. Feature Engineering Recipe
        feat_rec = {
            "polynomial_degree": 2 if ("REGRESSION" in str(family).upper() or "CLASSIFICATION" in str(family).upper()) else 1,
            "interaction_features": True if ("CLASSIFICATION" in str(family).upper() or "REGRESSION" in str(family).upper() or "TWIN" in str(family).upper()) else False,
            "pca_components": 5 if ("VISION" in str(family).upper() or "ANOMALY" in str(family).upper()) else 0,
            "feature_selection_method": "k_best" if ("CLASSIFICATION" in str(family).upper() or "REGRESSION" in str(family).upper()) else "none",
            "k_best_features": 15,
            "create_aggregate_features": True
        }

        # 3. Splitting Recipe
        split_rec = {
            "test_size": 0.2,
            "validation_strategy": pa.get("validation", "stratified_kfold"),
            "random_state": 42
        }

        # 4. Training Recipe
        train_rec = {
            "algorithm": algo,
            "variant": variant,
            "validation_metrics": get_metrics_for_family(family),
            "hyperparameters": get_hyperparameters(algo, variant)
        }

        # Save files
        with open(os.path.join(PREPARING_DIR, f"{dag_id}.json"), "w", encoding="utf-8") as pf:
            json.dump(prep_rec, pf, indent=4)

        with open(os.path.join(FEATURE_ENG_DIR, f"{dag_id}.json"), "w", encoding="utf-8") as ff:
            json.dump(feat_rec, ff, indent=4)

        with open(os.path.join(SPLITTING_DIR, f"{dag_id}.json"), "w", encoding="utf-8") as sf:
            json.dump(split_rec, sf, indent=4)

        with open(os.path.join(TRAINING_DIR, f"{dag_id}.json"), "w", encoding="utf-8") as tf:
            json.dump(train_rec, tf, indent=4)

        count += 1

    print(f"Successfully generated 4-part recipe sets for {count} DAG IDs!")

if __name__ == "__main__":
    main()
