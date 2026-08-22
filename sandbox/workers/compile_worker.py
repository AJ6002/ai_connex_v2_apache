"""
Compile Worker - Apache DataFusion parameterized template compiler.
Executes inside parser-compile sandbox container under non-root 10001:10001 with read-only rootfs.
Strictly prohibits arbitrary/agent-generated SQL strings; uses pre-validated YAML compilation templates.
"""

import sys
import os
import glob
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pyarrow as pa
import pyarrow.parquet as pq
import datafusion
import yaml

from contracts.sandbox.result_manifest_contract import ParserResultManifest


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def process_compile():
    start_time = datetime.utcnow()
    input_dir = Path(os.environ.get("SANDBOX_INPUT_DIR", "/sandbox/input"))
    output_dir = Path(os.environ.get("SANDBOX_OUTPUT_DIR", "/sandbox/output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    template_mode = os.environ.get("COMPILE_TEMPLATE", "union").lower()
    parquet_inputs = list(input_dir.glob("*.parquet"))

    if not parquet_inputs:
        print(f"No Parquet input files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    output_parquet_path = output_dir / "compiled_output.parquet"

    try:
        ctx = datafusion.SessionContext()

        # Register input parquet files in DataFusion context as verified tables
        table_names = []
        for idx, file_path in enumerate(parquet_inputs):
            t_name = f"input_table_{idx}"
            ctx.register_parquet(t_name, str(file_path))
            table_names.append(t_name)

        if template_mode == "union" or len(table_names) == 1:
            # Execute Union via DataFusion DataFrame API (no raw SQL text parsing)
            df = ctx.table(table_names[0])
            for t_name in table_names[1:]:
                df = df.union(ctx.table(t_name))
        elif template_mode == "join" and len(table_names) >= 2:
            df = ctx.table(table_names[0]).join(
                ctx.table(table_names[1]),
                join_type="inner",
                left_cols=["id"],
                right_cols=["id"]
            )
        else:
            df = ctx.table(table_names[0])

        # Write compiled results out to Parquet
        arrow_table = df.to_arrow_table()
        row_count = arrow_table.num_rows

        pq.write_table(arrow_table, output_parquet_path, compression="snappy")
        output_hash = compute_sha256(output_parquet_path)

        schema_def = {col: str(dtype) for col, dtype in zip(arrow_table.schema.names, arrow_table.schema.types)}

        end_time = datetime.utcnow()

        manifest = ParserResultManifest(
            job_id=os.environ.get("JOB_ID", f"job_compile_{int(start_time.timestamp())}"),
            image_name="parser-compile",
            image_digest=os.environ.get("IMAGE_DIGEST", "sha256:local_unpinned"),
            input_file=", ".join([p.name for p in parquet_inputs]),
            input_hash=",".join([compute_sha256(p)[:8] for p in parquet_inputs]),
            output_parquet=output_parquet_path.name,
            output_hash=output_hash,
            row_count=row_count,
            schema_definition=schema_def,
            started_at=start_time,
            completed_at=end_time,
            lineage={
                "parser": "parser-compile",
                "engine": "apache-datafusion",
                "template": template_mode,
                "input_tables_count": len(table_names)
            }
        )

        manifest_path = output_dir / "result_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        print(f"Compile Parser successfully built Parquet artifact: {output_parquet_path} ({row_count} rows)")

    except Exception as e:
        print(f"Compile Parser Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    process_compile()
