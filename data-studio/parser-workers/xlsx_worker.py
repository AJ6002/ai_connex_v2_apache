"""
XLSX Parser Worker Container Entrypoint.
"""

import sys
import os
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def parse_xlsx(input_xlsx_path: str, output_dir: str):
    if not os.path.exists(input_xlsx_path):
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_excel(input_xlsx_path)
    table = pa.Table.from_pandas(df)

    output_parquet_path = os.path.join(output_dir, "dataset.parquet")
    pq.write_table(table, output_parquet_path, compression="SNAPPY")

    schema_map = {name: str(type_) for name, type_ in zip(table.schema.names, table.schema.types)}

    with open(os.path.join(output_dir, "schema.json"), "w") as f:
        json.dump(schema_map, f, indent=2)

    print(f"Parsed XLSX: {table.num_rows} rows")

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "/home/appuser/app/input.xlsx"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "/home/appuser/app/output"
    parse_xlsx(input_file, out_dir)
