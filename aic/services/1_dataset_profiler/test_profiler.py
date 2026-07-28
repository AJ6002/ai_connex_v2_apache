import pandas as pd
import numpy as np
from profiler import generate_profile
from detector import detect_family

def test_regression_dataset():
    print("Testing regression dataset...")
    np.random.seed(42)
    x = np.random.rand(100)
    y = 2 * x + np.random.normal(0, 0.1, 100)
    df = pd.DataFrame({'feature1': x, 'target': y})
    
    profile = generate_profile(df)
    family_res = detect_family(df, profile)
    
    print("Detected Family:", family_res['algorithm_family'])
    print("Confidence:", family_res['family_confidence'])
    print("Suggested Task:", family_res['suggested_task'])
    print("Reason:", family_res['reason'])
    print("Target Col:", family_res['target_column'])
    assert family_res['algorithm_family'] == 'Regression'
    assert family_res['suggested_task'] == 'Regression'
    print("Regression test PASSED!\n")

def test_anomaly_dataset():
    print("Testing anomaly detection dataset...")
    np.random.seed(42)
    # Generate normal data
    data = np.random.normal(10, 2, (100, 3))
    # Inject outliers
    data[0] = [100, 200, 300]
    data[1] = [-100, -200, -300]
    data[2] = [80, 90, 100]
    data[3] = [-80, -90, -100]
    
    df = pd.DataFrame(data, columns=['feat1', 'feat2', 'feat3'])
    
    profile = generate_profile(df)
    family_res = detect_family(df, profile)
    
    print("Detected Family:", family_res['algorithm_family'])
    print("Confidence:", family_res['family_confidence'])
    print("Suggested Task:", family_res['suggested_task'])
    print("Reason:", family_res['reason'])
    assert family_res['algorithm_family'] == 'Anomaly Detection'
    print("Anomaly Detection test PASSED!\n")

def test_classification_dataset():
    print("Testing classification dataset (Miscellaneous)...")
    df = pd.DataFrame({
        'age': [25, 30, 45, 35, 22, 60],
        'salary': [50000, 80000, 120000, 90000, 40000, 150000],
        'churn': ['No', 'Yes', 'No', 'No', 'Yes', 'No']
    })
    
    profile = generate_profile(df)
    family_res = detect_family(df, profile)
    
    print("Detected Family:", family_res['algorithm_family'])
    print("Confidence:", family_res['family_confidence'])
    print("Suggested Task:", family_res['suggested_task'])
    print("Reason:", family_res['reason'])
    print("Target Col:", family_res['target_column'])
    assert family_res['algorithm_family'] == 'Miscellaneous'
    assert 'Classification' in family_res['suggested_task']
    print("Classification test PASSED!\n")

if __name__ == "__main__":
    test_regression_dataset()
    test_anomaly_dataset()
    test_classification_dataset()
    print("All tests passed successfully!")
