"""
Lightweight Dataset Inspector - Safe metadata and candidate schema discovery.
"""

import os
import zipfile
import tarfile
from typing import Dict, Any, List, Optional
from contracts.discovery.discovery_contract import DatasetDiscoveryArtifact

def inspect_dataset_archive(file_path: str, asset_id: str) -> DatasetDiscoveryArtifact:
    """
    Perform cheap, safe metadata inspection over a dataset archive without full uncompressed extraction.
    """
    if not os.path.exists(file_path):
        return DatasetDiscoveryArtifact(
            asset_id=asset_id,
            is_safe=False,
            security_findings=[f"File not found: {file_path}"]
        )

    security_findings: List[str] = []
    member_inventory: List[str] = []
    member_sizes: Dict[str, int] = {}
    detected_formats: List[str] = []

    file_size = os.path.getsize(file_path)
    # Security limits
    MAX_ARCHIVE_SIZE = 500 * 1024 * 1024  # 500 MB limit
    if file_size > MAX_ARCHIVE_SIZE:
        security_findings.append(f"Archive exceeds maximum size limit ({file_size} bytes)")

    if file_path.endswith(".zip"):
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                for info in z.infolist():
                    name = info.filename
                    # Security checks against Zip Slip
                    if name.startswith("/") or ".." in name:
                        security_findings.append(f"Path traversal risk rejected: {name}")
                        continue
                    member_inventory.append(name)
                    member_sizes[name] = info.file_size
                    ext = name.split(".")[-1].lower()
                    if ext in ["csv", "xlsx", "json", "parquet"] and ext not in detected_formats:
                        detected_formats.append(ext)
        except Exception as e:
            security_findings.append(f"Invalid or corrupted ZIP archive: {str(e)}")

    return DatasetDiscoveryArtifact(
        asset_id=asset_id,
        archive_type="zip" if file_path.endswith(".zip") else "none",
        member_inventory=member_inventory,
        member_sizes=member_sizes,
        detected_formats=detected_formats,
        security_findings=security_findings,
        is_safe=len(security_findings) == 0
    )
