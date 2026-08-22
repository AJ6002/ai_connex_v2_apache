"""
Parquet Inspection Worker - Minimal schema and statistics validator for Parquet inputs.
Executes inside parser-parquet sandbox container under non-root 10001:10001 with read-only rootfs.
"""

import sys
import os
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

import pyarrow.parquet as pq

from contracts.sandbox.result_manifest_contract import ParserResultManifest


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def process_parquet():
    start_time = datetime.utcnow()
    input_dir = Path(os.environ.get("SANDBOX_INPUT_DIR", "/sandbox/input"))
    output_dir = Path(os.environ.get("SANDBOX_OUTPUT_DIR", "/sandbox/output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    input_files = list(input_dir.glob("*.parquet")) + list(input_dir.glob("*.pq"))
    if not input_files:
        print(f"No Parquet input files found in {input_dir}")
        sys.exit(1)

    input_path = input_files[0]
    input_hash = compute_sha256(input_path)

    output_parquet_path = output_dir / input_path.name

    try:
        # Inspect Parquet metadata without loading full dataset into RAM
        parquet_file = pq.ParquetFile(input_path)
        meta = parquet_file.metadata
        row_count = meta.num_rows
        schema = parquet_file.schema_arrow

        # Copy/Validate to output
        shutil.copy2(input_path, output_parquet_path)
        output_hash = compute_sha256(output_parquet_path)

        schema_def = {col: str(dtype) for col, dtype in zip(schema.names, schema.types)}

        end_time = datetime.utcnow()

        manifest = ParserResultManifest(
            job_id=os.environ.get("JOB_ID", f"job_parquet_{int(start_time.timestamp())}"),
            image_name="parser-parquet",
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
                "parser": "parser-parquet",
                "engine": "pyarrow",
                "num_row_groups": meta.num_row_groups,
                "format": "parquet"
            }
        )

        manifest_path = output_dir / "result_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        print(f"Parquet Parser successfully validated & output artifact: {output_parquet_path} ({row_count} rows)")

    except Exception as e:
        print(f"Parquet Parser Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    process_parquet()
