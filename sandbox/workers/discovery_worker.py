"""
Discovery Worker - Stage 1-5 safe dataset inspection and structural segmentation.
Executes inside the parser-discovery sandbox container under user 10001:10001 with read-only rootfs.
"""

import sys
import os
import json
import zipfile
import tarfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import polars as pl

# Import contracts from sandbox context
from contracts.segmentation.segmentation_contract import CandidateRegion, SegmentationProposal
from contracts.discovery.discovery_contract import DatasetDiscoveryArtifact


def inspect_archive(input_path: Path) -> Tuple[Optional[str], List[str], Dict[str, int]]:
    """Stage 1: Archive inspection with security zip-slip & traversal safeguards."""
    member_inventory: List[str] = []
    member_sizes: Dict[str, int] = {}
    archive_type: Optional[str] = None

    if zipfile.is_zipfile(input_path):
        archive_type = "zip"
        with zipfile.ZipFile(input_path, 'r') as zf:
            for member in zf.infolist():
                # Zip-slip prevention
                if ".." in member.filename or member.filename.startswith("/"):
                    continue
                member_inventory.append(member.filename)
                member_sizes[member.filename] = member.file_size
    elif tarfile.is_tarfile(input_path):
        archive_type = "tar"
        with tarfile.TarFile.open(input_path, 'r') as tf:
            for member in tf.getmembers():
                if ".." in member.name or member.name.startswith("/"):
                    continue
                member_inventory.append(member.name)
                member_sizes[member.name] = member.size
    else:
        archive_type = "none"
        member_inventory.append(input_path.name)
        member_sizes[input_path.name] = input_path.stat().st_size

    return archive_type, member_inventory, member_sizes


def load_vocabularies() -> List[str]:
    """Load standard industrial vocabulary from registries."""
    vocab: List[str] = ["timestamp", "datetime", "date", "id", "device_id", "value", "status", "production", "qa", "htds", "ltda"]
    registry_dir = Path("/sandbox/registries")
    if not registry_dir.exists():
        registry_dir = Path(__file__).parent.parent.parent / "registries"

    if registry_dir.exists():
        for file_path in registry_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        vocab.extend(data.keys())
                    elif isinstance(data, list):
                        vocab.extend([str(item) for item in data])
            except Exception:
                pass
    return list(set(vocab))


def analyze_tabular_structure(file_path: Path, vocab: List[str]) -> List[CandidateRegion]:
    """Stages 2–5: Structural segmentation, header detection, metadata row detection, semantic column matching."""
    regions: List[CandidateRegion] = []
    
    if file_path.suffix.lower() in [".csv", ".txt", ".tsv"]:
        try:
            # Read first 100 lines for inspection
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [f.readline().strip() for _ in range(100)]
                lines = [l for l in lines if l]

            if not lines:
                return regions

            metadata_rows = 0
            header_idx = 0
            best_vocab_score = 0
            best_header: List[str] = []

            for idx, line in enumerate(lines[:10]):
                parts = [p.strip().strip('"').strip("'") for p in line.split(",") if p.strip()]
                if not parts:
                    continue
                score = sum(1 for p in parts if any(v in p.lower() for v in vocab))
                if score > best_vocab_score:
                    best_vocab_score = score
                    header_idx = idx
                    best_header = parts

            metadata_rows = header_idx
            
            # Infer row boundaries
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                total_lines = sum(1 for _ in f)

            matched_vocab = [p for p in best_header if any(v in p.lower() for v in vocab)]
            confidence = min(0.95, 0.50 + (0.10 * len(matched_vocab))) if best_header else 0.40

            adjudication_log = [
                f"Metadata rows detected: {metadata_rows}",
                f"Header detected at line {header_idx + 1}: {best_header[:5]}",
                f"Matched {len(matched_vocab)} vocabulary terms: {matched_vocab[:5]}"
            ]

            region = CandidateRegion(
                source_file=file_path.name,
                row_start=header_idx,
                row_end=max(0, total_lines - 1),
                col_start=0,
                col_end=max(0, len(best_header) - 1),
                detected_header=best_header,
                matched_vocabulary=matched_vocab,
                confidence=confidence,
                proposed_table_name=file_path.stem.lower().replace(" ", "_"),
                adjudication_log=adjudication_log
            )
            regions.append(region)

        except Exception as e:
            pass

    return regions


def run_discovery():
    input_dir = Path(os.environ.get("SANDBOX_INPUT_DIR", "/sandbox/input"))
    output_dir = Path(os.environ.get("SANDBOX_OUTPUT_DIR", "/sandbox/output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    input_files = list(input_dir.glob("*"))
    if not input_files:
        print(f"No input files found in {input_dir}")
        sys.exit(1)

    target_file = input_files[0]
    archive_type, inventory, sizes = inspect_archive(target_file)
    vocab = load_vocabularies()
    regions = analyze_tabular_structure(target_file, vocab)

    low_confidence = any(r.confidence < 0.85 for r in regions) or not regions

    proposal = SegmentationProposal(
        asset_id=target_file.stem,
        pipeline_version="1.0.0",
        regions=regions,
        requires_adjudication=low_confidence,
        adjudication_threshold=0.85,
        created_at=datetime.utcnow()
    )

    artifact = DatasetDiscoveryArtifact(
        asset_id=target_file.stem,
        archive_type=archive_type,
        member_inventory=inventory,
        member_sizes=sizes,
        detected_formats=[target_file.suffix.lstrip(".")],
        sample_headers={r.proposed_table_name: r.detected_header for r in regions},
        segmentation_proposal=proposal,
        is_safe=True
    )

    # Write output artifacts
    output_proposal_path = output_dir / "segmentation_proposal.json"
    with open(output_proposal_path, "w", encoding="utf-8") as f:
        f.write(proposal.model_dump_json(indent=2))

    output_discovery_path = output_dir / "discovery_artifact.json"
    with open(output_discovery_path, "w", encoding="utf-8") as f:
        f.write(artifact.model_dump_json(indent=2))

    print(f"Stage 1-5 Discovery Complete. Proposal written to {output_proposal_path}")


if __name__ == "__main__":
    run_discovery()
