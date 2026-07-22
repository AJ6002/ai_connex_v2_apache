"""
aiconnex_zip_compiler — AIConnex Universal Multi-Table Dataset Compiler
========================================================================
Decoupled, domain-agnostic data ingestion compiler for multi-file ZIP archives.

Four Internal Layers:
  Layer 1: Discovery         (file role, entity & timestamp detection)
  Layer 2: Schema Mapping    (timestamp normalization & column mapping)
  Layer 3: Relational Join   (composite key join & Cartesian explosion guard)
  Layer 4: ML Handoff        (merged CSVs + join_audit.json + schema_map.json)
"""

from __future__ import annotations

from .compiler import UnifiedCompiler, CompileResult

__version__ = "1.0.0"
__all__ = ["UnifiedCompiler", "CompileResult"]
