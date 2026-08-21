"""
CSV Parser Worker Container Entrypoint - Parses CSV into Parquet & metadata JSON.
"""

import sys
import os
import json
import pyarrow.csv as pv
import pyarrow.parquet as pq

def parse_csv(input_csv_path: str, output_dir: str):
    """
    Parse untrusted CSV into PyArrow Table and write canonical Parquet & metadata.
    """
    if not os.path.exists(input_csv_path):
        print(f"Error: Input file {input_csv_path} does not exist.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    table = pv.read_csv(input_csv_path)

    output_parquet_path = os.path.join(output_dir, "dataset.parquet")
    pq.write_table(table, output_parquet_path, compression="SNAPPY")

    schema_map = {name: str(type_) for name, type_ in zip(table.schema.names, table.schema.types)}
    
    metadata = {
        "status": "MACHINE_READY",
        "row_count": table.num_rows,
        "column_count": table.num_columns,
        "schema_map": schema_map,
        "parquet_path": output_parquet_path
    }

    with open(os.path.join(output_dir, "schema.json"), "w") as f:
        json.dump(schema_map, f, indent=2)

    with open(os.path.join(output_dir, "parser_result.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Successfully parsed {table.num_rows} rows into {output_parquet_path}")

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "/home/appuser/app/input.csv"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "/home/appuser/app/output"
    parse_csv(input_file, out_dir)
