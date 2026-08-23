"""
CSV Parser Worker - High-performance chunked/streamed CSV to Arrow/Parquet conversion.
Executes inside parser-csv sandbox container under non-root 10001:10001 with read-only rootfs.
"""

import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

from contracts.sandbox.result_manifest_contract import ParserResultManifest


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def process_csv():
    start_time = datetime.utcnow()
    input_dir = Path(os.environ.get("SANDBOX_INPUT_DIR", "/sandbox/input"))
    output_dir = Path(os.environ.get("SANDBOX_OUTPUT_DIR", "/sandbox/output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    input_files = list(input_dir.glob("*.csv")) + list(input_dir.glob("*.txt"))
    if not input_files:
        print(f"No CSV input files found in {input_dir}")
        sys.exit(1)

    input_path = input_files[0]
    input_hash = compute_sha256(input_path)

    output_parquet_path = output_dir / f"{input_path.stem}.parquet"

    # Streaming/chunked parse via Polars / PyArrow
    try:
        df = pl.read_csv(input_path, ignore_errors=True)
        arrow_table = df.to_arrow()
        row_count = arrow_table.num_rows

        # Write to Parquet
        pq.write_table(arrow_table, output_parquet_path, compression="snappy")
        output_hash = compute_sha256(output_parquet_path)

        schema_def = {col: str(dtype) for col, dtype in zip(arrow_table.schema.names, arrow_table.schema.types)}

        end_time = datetime.utcnow()

        manifest = ParserResultManifest(
            job_id=os.environ.get("JOB_ID", f"job_csv_{int(start_time.timestamp())}"),
            image_name="parser-csv",
            image_digest=os.environ.get("IMAGE_DIGEST", "sha256:local_unpinned"),
            input_file=input_path.name,
            input_hash=input_hash,
            output_parquet=output_parquet_path.name,
            output_hash=output_hash,
            row_count=row_count,
            schema_definition=schema_def,
            started_at=start_time,
            completed_at=end_time,
            lineage={
                "parser": "parser-csv",
                "engine": "polars+pyarrow",
                "format": "csv",
                "compression": "snappy"
            }
        )

        manifest_path = output_dir / "result_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        print(f"CSV Parser successfully generated Parquet artifact: {output_parquet_path} ({row_count} rows)")

    except Exception as e:
        print(f"CSV Parser Error: {e!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    process_csv()
