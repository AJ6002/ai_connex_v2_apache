"""
generate_dag_mapping.py — Auto-generates dag_mapping.json from master Excel
"""

import json
from pathlib import Path
import pandas as pd

# Dynamic root resolution
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = BASE_DIR.parent.parent

excel_path = WORKSPACE_ROOT / "algorithm_families_complete.xlsx"
output_path_profiler = BASE_DIR / "dag_mapping.json"
output_path_dag = BASE_DIR.parent / "2_dag" / "dag_mapping.json"

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

# Write to 1_dataset_profiler
with open(output_path_profiler, "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)
print(f"Successfully generated {output_path_profiler}")

# Write to 2_dag
output_path_dag.parent.mkdir(parents=True, exist_ok=True)
with open(output_path_dag, "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)
print(f"Successfully generated {output_path_dag}")

print(f"Successfully generated DAG mappings with {len(mapping)} families and {len(df)} DAG mappings.")

