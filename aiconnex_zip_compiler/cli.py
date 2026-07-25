"""
cli.py — Command Line Interface for AIConnex Plugin Pipeline Compiler
======================================================================
Usage:
    # Interactive mode (TUI halts for user intent selection):
    python -m aiconnex_zip_compiler --input data.zip --output out/ --interactive

    # Batch mode (auto-selects default intent, no halt):
    python -m aiconnex_zip_compiler --input data.zip --output out/ --batch

    # Strategy override (bypasses TUI, uses specified strategy):
    python -m aiconnex_zip_compiler --input data.zip --output out/ --strategy failure_prediction
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import UnifiedCompiler, CompileResult


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="aiconnex_zip_compiler",
        description="AIConnex Universal Multi-Table Dataset Compiler with HITL Intent Layer",
    )
    parser.add_argument(
        "--input", "-i", required=True, metavar="PATH",
        help="Path to input ZIP archive or dataset directory.",
    )
    parser.add_argument(
        "--output", "-o", required=True, metavar="OUTPUT_DIR",
        help="Destination directory for compiled CSVs and audit JSON reports.",
    )

    # Intent Layer flags (mutually exclusive group)
    intent_group = parser.add_mutually_exclusive_group()
    intent_group.add_argument(
        "--interactive", action="store_true", default=False,
        help="Force interactive TUI mode (halts terminal for user intent selection).",
    )
    intent_group.add_argument(
        "--batch", action="store_true", default=False,
        help="Batch mode — auto-selects default intent option without prompting.",
    )
    intent_group.add_argument(
        "--strategy", metavar="STRATEGY_ID", type=str, default=None,
        help=(
            "Bypass TUI and use this strategy directly. "
            "Options: failure_prediction, anomaly_detection, forecasting, "
            "unified_all_conditions, separate_per_condition, auto_model"
        ),
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print detailed execution logs.",
    )

    args = parser.parse_args()

    zip_path = Path(args.input)
    output_dir = Path(args.output)

    if not zip_path.exists():
        print(f"Error: Input path not found at {zip_path}", file=sys.stderr)
        return 1

    # Determine interactive mode
    # Default: interactive if tty is attached and neither --batch nor --strategy is set
    interactive = args.interactive
    if not interactive and not args.batch and not args.strategy:
        # Auto-detect: interactive if stdin is a terminal
        interactive = hasattr(sys.stdin, "isatty") and sys.stdin.isatty()

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG, format="%(name)s | %(message)s")

    print(f"=== AIConnex Plugin Pipeline Compiler v0.9 ===")
    print(f"Input : {zip_path}")
    print(f"Output: {output_dir}")
    if args.strategy:
        print(f"Mode  : Strategy override ({args.strategy})")
    elif args.batch:
        print(f"Mode  : Batch (auto-select default)")
    elif interactive:
        print(f"Mode  : Interactive (TUI)")
    print()

    compiler = UnifiedCompiler(
        zip_path=zip_path,
        output_dir=output_dir,
        interactive=interactive,
        strategy_override=args.strategy,
    )
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
    print(f"    - {res.artifacts.compiler_report_json}")
    print(f"    - {res.output_dir / 'compiler_lock.json'}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
