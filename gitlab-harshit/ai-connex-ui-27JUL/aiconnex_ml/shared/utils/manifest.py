"""
manifest.py — Load / save manifest.json from S3, local filesystem, or SQLite.
==============================================================================
All pipeline steps accept and return the manifest dict.
This module ensures the manifest is always persisted after each step.
"""

from __future__ import annotations
import json
import os
from typing import Any, Dict


def _default_serializer(obj: Any) -> Any:
    """Cast numpy/pandas types to native Python for JSON serialization."""
    import numpy as np
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def load_manifest(path: str) -> Dict[str, Any]:
    """
    Load manifest from S3 URI (s3://bucket/key) or local path.
    Returns a plain dict — not a Pydantic model — so all pipeline steps
    can access and update fields freely without re-validation overhead.
    """
    if path.startswith("s3://"):
        import boto3
        from urllib.parse import urlparse
        parsed = urlparse(path)
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))
        return json.loads(obj["Body"].read().decode("utf-8"))
    else:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def save_manifest(manifest: Dict[str, Any], path: str) -> None:
    """
    Save manifest to S3 URI or local path.
    Automatically casts numpy types to native Python before serialization.
    """
    serialized = json.dumps(manifest, indent=2, default=_default_serializer)

    if path.startswith("s3://"):
        import boto3
        from urllib.parse import urlparse
        parsed = urlparse(path)
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=parsed.netloc,
            Key=parsed.path.lstrip("/"),
            Body=serialized.encode("utf-8"),
        )
    else:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(serialized)


def mark_step_complete(manifest: Dict[str, Any], step_name: str) -> Dict[str, Any]:
    """Append step_name to manifest['completed_steps'] and return manifest."""
    if "completed_steps" not in manifest:
        manifest["completed_steps"] = []
    if step_name not in manifest["completed_steps"]:
        manifest["completed_steps"].append(step_name)
    return manifest


def get_manifest_field(manifest: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely access nested manifest fields using dot-path keys."""
    node = manifest
    for key in keys:
        if not isinstance(node, dict):
            return default
        node = node.get(key, default)
        if node is default:
            return default
    return node
