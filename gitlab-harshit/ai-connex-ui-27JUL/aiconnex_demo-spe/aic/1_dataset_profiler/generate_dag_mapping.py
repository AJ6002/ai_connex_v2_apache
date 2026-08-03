"""
generate_dag_mapping.py — Auto-generates dag_mapping.json from master Excel
"""

import json
from pathlib import Path
import pandas as pd

excel_path = Path(r"X:\TAS\AICONNEX\algorithm_families_complete-2.xlsx")
output_path = Path(r"X:\TAS\AICONNEX\aic\1_dataset_profiler\dag_mapping.json")

df = pd.read_excel(excel_path)
print(f"Read {len(df)} rows from {excel_path}")

mapping = {}
for family_name, group in df.groupby("FAMILY_NAME"):
    rows = []
    for _, row in group.iterrows():
        rows.append({
            "dag_id": str(row["DAG ID"]),
            "family_id": str(row["FAMILY_ID"]),
            "algorithm": str(row["Algorithm"]),
            "variant": str(row["Variant"]),
            "special_handling": str(row["Special Handling"]) if pd.notna(row["Special Handling"]) else None
        })
    mapping[family_name] = rows

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=2)

print(f"Successfully generated {output_path} with {len(mapping)} families and {len(df)} DAG mappings.")
