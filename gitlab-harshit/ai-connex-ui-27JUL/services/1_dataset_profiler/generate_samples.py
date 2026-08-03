import os
import pandas as pd
import numpy as np

def generate():
    os.makedirs('samples', exist_ok=True)
    
    # 1. Regression Sample (Housing)
    print("Generating regression_sample.csv...")
    np.random.seed(42)
    n_samples = 500
    size = np.random.normal(1500, 300, n_samples)
    rooms = np.random.choice([1, 2, 3, 4, 5], size=n_samples, p=[0.1, 0.3, 0.4, 0.15, 0.05])
    age = np.random.uniform(1, 50, n_samples)
    # price = 100 * size + 25000 * rooms - 1000 * age + noise
    price = 100 * size + 25000 * rooms - 1000 * age + np.random.normal(0, 5000, n_samples)
    
    df_reg = pd.DataFrame({
        'house_id': [f"H_{i:04d}" for i in range(n_samples)],
        'square_feet': size,
        'num_rooms': rooms,
        'property_age_years': age,
        'sale_price_usd': price
    })
    df_reg.to_csv('samples/housing_regression.csv', index=False)
    
    # 2. Anomaly Sample (Unlabeled sensors)
    print("Generating anomaly_sample.csv...")
    n_sensor_samples = 1000
    timestamps = pd.date_range(start='2026-07-19 00:00:00', periods=n_sensor_samples, freq='min')
    
    # Normal state sensor values
    temperature = np.random.normal(25.0, 1.2, n_sensor_samples)
    pressure = np.random.normal(101.3, 0.5, n_sensor_samples)
    vibration = np.random.normal(0.02, 0.005, n_sensor_samples)
    
    # Inject 4% random anomalies
    anomaly_indices = np.random.choice(n_sensor_samples, size=40, replace=False)
    for idx in anomaly_indices:
        # Some are high temperature spikes
        if np.random.rand() > 0.5:
            temperature[idx] += np.random.uniform(15, 25)
            vibration[idx] += np.random.uniform(0.05, 0.1)
        else: # Some are sudden pressure drops
            pressure[idx] -= np.random.uniform(4.0, 8.0)
            vibration[idx] += np.random.uniform(0.06, 0.15)
            
    df_anomaly = pd.DataFrame({
        'timestamp': timestamps,
        'temp_celsius': temperature,
        'pressure_kpa': pressure,
        'vibration_amplitude': vibration
    })
    df_anomaly.to_csv('samples/sensors_anomaly.csv', index=False)
    
    # 3. Classification / Miscellaneous Sample (Churn)
    print("Generating churn_classification.csv...")
    n_churn_samples = 400
    usage_mins = np.random.normal(300, 80, n_churn_samples)
    support_calls = np.random.choice([0, 1, 2, 3, 4, 5, 6], size=n_churn_samples, p=[0.5, 0.25, 0.12, 0.06, 0.04, 0.02, 0.01])
    contract_type = np.random.choice(['Month-to-month', 'One year', 'Two year'], size=n_churn_samples, p=[0.6, 0.25, 0.15])
    
    # Simple rule for churn probability
    churn_prob = 1 / (1 + np.exp(-(-3 + 0.005 * usage_mins + 0.6 * support_calls + (1.2 if contract_type[0] == 'Month-to-month' else 0))))
    churn = np.random.rand(n_churn_samples) < churn_prob
    churn_labels = ['Yes' if c else 'No' for c in churn]
    
    df_churn = pd.DataFrame({
        'customer_id': [f"C_{i:04d}" for i in range(n_churn_samples)],
        'monthly_usage_minutes': usage_mins,
        'support_calls_count': support_calls,
        'contract': contract_type,
        'churn': churn_labels
    })
    df_churn.to_csv('samples/churn_classification.csv', index=False)
    print("All samples generated in dataset_profiler/samples/")

if __name__ == '__main__':
    generate()
