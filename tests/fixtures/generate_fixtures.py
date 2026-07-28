"""
Synthetic mini-dataset generator for local pipeline tests.
Produces a clean 200-row parquet file with 5 engines x 40 cycles.
Run once before running tests.
"""
import os
import numpy as np
import pandas as pd

SENSORS = ["sensor_2", "sensor_3", "sensor_4", "sensor_7", "sensor_8",
           "sensor_9", "sensor_11", "sensor_12", "sensor_13"]
SETTINGS = ["setting_1", "setting_2", "setting_3"]

np.random.seed(42)

rows = []
for engine_id in range(1, 6):
    max_cycle = 40
    for cycle in range(1, max_cycle + 1):
        rul = max_cycle - cycle
        row = {
            "global_engine_id": engine_id,
            "cycle": cycle,
            "RUL": rul,
        }
        for s in SENSORS:
            row[s] = float(np.random.normal(loc=50.0, scale=5.0))
        for s in SETTINGS:
            row[s] = float(np.random.uniform(0.0, 1.0))
        rows.append(row)

df = pd.DataFrame(rows)

out_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(out_dir, "mini_dataset.parquet")
df.to_parquet(out_path, index=False)
print(f"Saved mini_dataset.parquet -> {out_path}  ({df.shape[0]} rows x {df.shape[1]} cols)")
