"""
Shared pytest fixtures and conftest for all pipeline tests.
"""
import os
import json
import pytest
import numpy as np
import pandas as pd

FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__))
MINI_DATASET = os.path.join(FIXTURES_DIR, "mini_dataset.parquet")
MINI_CONFIG  = os.path.join(FIXTURES_DIR, "mini_config.json")

SENSORS  = ["sensor_2", "sensor_3", "sensor_4", "sensor_7", "sensor_8",
            "sensor_9", "sensor_11", "sensor_12", "sensor_13"]
SETTINGS = ["setting_1", "setting_2", "setting_3"]


@pytest.fixture(scope="session")
def mini_config():
    with open(MINI_CONFIG) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def mini_df():
    """Build mini dataset in-memory; does NOT require generate_fixtures.py."""
    np.random.seed(42)
    rows = []
    for engine_id in range(1, 6):
        max_cycle = 40
        for cycle in range(1, max_cycle + 1):
            row = {"global_engine_id": engine_id, "cycle": cycle, "RUL": max_cycle - cycle}
            for s in SENSORS:
                row[s] = float(np.random.normal(50.0, 5.0))
            for s in SETTINGS:
                row[s] = float(np.random.uniform(0.0, 1.0))
            rows.append(row)
    return pd.DataFrame(rows)
