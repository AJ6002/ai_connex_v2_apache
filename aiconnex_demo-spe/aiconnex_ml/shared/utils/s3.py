"""
s3.py — S3 upload/download helpers
====================================
Wraps boto3 for uploading/downloading files and directories.
Falls back gracefully if boto3 is not available (local-only mode).
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional


def _get_client():
    try:
        import boto3
        return boto3.client("s3")
    except ImportError:
        raise ImportError("boto3 is required for S3 operations. Install with: pip install boto3")


def upload_file(local_path: str, bucket: str, s3_key: str) -> str:
    """Upload a local file to S3. Returns the s3:// URI."""
    s3 = _get_client()
    s3.upload_file(local_path, bucket, s3_key)
    uri = f"s3://{bucket}/{s3_key}"
    print(f"[S3] Uploaded: {local_path} → {uri}")
    return uri


def download_file(bucket: str, s3_key: str, local_path: str) -> str:
    """Download an S3 object to a local path. Returns local_path."""
    s3 = _get_client()
    os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
    s3.download_file(bucket, s3_key, local_path)
    print(f"[S3] Downloaded: s3://{bucket}/{s3_key} → {local_path}")
    return local_path


def upload_directory(local_dir: str, bucket: str, s3_prefix: str) -> None:
    """Recursively upload a local directory to S3 under the given prefix."""
    s3 = _get_client()
    for root, _, files in os.walk(local_dir):
        for file in files:
            local_file = os.path.join(root, file)
            relative = os.path.relpath(local_file, local_dir)
            s3_key = f"{s3_prefix.rstrip('/')}/{relative.replace(os.sep, '/')}"
            s3.upload_file(local_file, bucket, s3_key)
    print(f"[S3] Directory uploaded: {local_dir} → s3://{bucket}/{s3_prefix}")


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parse 's3://bucket/key' → ('bucket', 'key')."""
    from urllib.parse import urlparse
    parsed = urlparse(uri)
    return parsed.netloc, parsed.path.lstrip("/")


def s3_uri_exists(uri: str) -> bool:
    """Return True if an S3 object exists at the given URI."""
    try:
        s3 = _get_client()
        bucket, key = parse_s3_uri(uri)
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False
