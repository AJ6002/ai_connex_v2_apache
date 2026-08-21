"""
Parquet Inspection Worker Container Entrypoint.
"""

import sys
import os
import json
import pyarrow.parquet as pq

def parse_parquet(input_parquet_path: str, output_dir: str):
    if not os.path.exists(input_parquet_path):
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    metadata = pq.read_metadata(input_parquet_path)
    schema = pq.read_schema(input_parquet_path)

    schema_map = {name: str(type_) for name, type_ in zip(schema.names, schema.types)}
    info = {
        "num_rows": metadata.num_rows,
        "num_columns": metadata.num_columns,
        "num_row_groups": metadata.num_row_groups,
        "schema_map": schema_map
    }

    with open(os.path.join(output_dir, "parser_result.json"), "w") as f:
        json.dump(info, f, indent=2)

    print(f"Inspected Parquet: {metadata.num_rows} rows across {metadata.num_row_groups} row groups")

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "/home/appuser/app/input.parquet"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "/home/appuser/app/output"
    parse_parquet(input_file, out_dir)
