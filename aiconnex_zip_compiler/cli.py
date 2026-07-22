"""
cli.py — Standalone Command Line Interface for aiconnex_zip_compiler
====================================================================
Usage:
    python -m aiconnex_zip_compiler --input data/raw/Solar\ Power\ Generation\ Data.zip --output workspace_data/solar_compiled
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compiler import UnifiedCompiler, CompileResult


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="aiconnex_zip_compiler",
        description="AIConnex Universal Multi-Table Dataset Compiler",
    )
    parser.add_argument(
        "--input", "-i", required=True, metavar="ZIP_PATH",
        help="Path to input ZIP archive.",
    )
    parser.add_argument(
        "--output", "-o", required=True, metavar="OUTPUT_DIR",
        help="Destination directory for compiled CSVs and audit JSON reports.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print detailed execution logs.",
    )

    args = parser.parse_args()

    zip_path = Path(args.input)
    output_dir = Path(args.output)

    if not zip_path.exists():
        print(f"Error: Input ZIP archive not found at {zip_path}", file=sys.stderr)
        return 1

    print(f"=== AIConnex Universal ZIP Compiler v1.0 ===")
    print(f"Input Path: {zip_path}")
    print(f"Output    : {output_dir}\n")

    compiler = UnifiedCompiler(zip_path, output_dir)
    res: CompileResult = compiler.compile()

    if not res.success:
        print(f"\n[FAIL] Compilation failed: {res.error}", file=sys.stderr)
        return 1

    print(f"[SUCCESS] Compiled in {res.duration_seconds}s")
    print(f"  Per-Group Merged CSVs:")
    for f in res.merged_files:
        print(f"    - {f}")
    if res.combined_file:
        print(f"  Combined Fleet CSV:\n    - {res.combined_file}")
    print(f"\n  Artifacts Written:")
    print(f"    - {res.artifacts.join_audit_json}")
    print(f"    - {res.artifacts.schema_map_json}")
    print(f"    - {res.artifacts.compiler_report_json}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
