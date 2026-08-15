"""
scripts/industrial_kb_sprint3_harvester.py

Phase 0: Automated Raw Knowledge Harvester & Source Register for Sprint 3 (ML Methodology KB).
Registers all 10 ML methodology source PDFs from `ML-knowledge-graph/` into:
1. `aiconnex_knowledge/01_source_register/source_register.json` (Approved status, domain="ml_methodology").
2. `aiconnex_knowledge/06_raw_documents/ml_methodology/` (Raw storage).
3. Generates `source_manifest.json` audit log with SHA-256 hashes and file metrics.
"""

import os
import shutil
import json
import hashlib
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MLMethodologyHarvester")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(BASE_DIR, "ML-knowledge-graph")
RAW_DOCS_DIR = os.path.join(BASE_DIR, "aiconnex_knowledge", "06_raw_documents", "ml_methodology")
SOURCE_REGISTER_FILE = os.path.join(BASE_DIR, "aiconnex_knowledge", "01_source_register", "source_register.json")
MANIFEST_FILE = os.path.join(BASE_DIR, "aiconnex_knowledge", "01_source_register", "ml_source_manifest.json")

# Metadata mapping for ML methodology PDFs
ML_CORPUS_MAP = {
    "CRISP-DM.pdf": {
        "source_id": "PLAT-DOC-ML-001",
        "title": "CRISP-DM 1.0 Step-by-Step Data Mining Guide",
        "source_type": "Methodology Standard",
        "authority_level": "A",
        "owner": "SPSS / CRISP-DM Consortium"
    },
    "Vogl2016 (review of diag-prog and best practices for manufacturing).pdf.pdf": {
        "source_id": "PLAT-DOC-ML-002",
        "title": "NIST Review of Diagnostic and Prognostic Capabilities and Best Practices for Manufacturing",
        "source_type": "Government Standard / Technical Review",
        "authority_level": "A",
        "owner": "NIST"
    },
    "2003.05155v2.pdf": {
        "source_id": "PLAT-DOC-ML-003",
        "title": "CRISP-ML(Q) The Machine Learning Lifecycle Process Model",
        "source_type": "Process Standard",
        "authority_level": "A",
        "owner": "CRISP-ML Consortium"
    },
    "1708.04649v1.pdf": {
        "source_id": "PLAT-DOC-ML-004",
        "title": "Deep Learning and Machine Learning Methodology Survey",
        "source_type": "Academic Survey",
        "authority_level": "A",
        "owner": "arXiv ML"
    },
    "TKDE_Data_Science_Trajectories_PF.pdf": {
        "source_id": "PLAT-DOC-ML-005",
        "title": "IEEE TKDE Data Science Trajectories and Analytics Framework",
        "source_type": "IEEE Journal Paper",
        "authority_level": "A",
        "owner": "IEEE TKDE"
    },
    "Wang3062024JOBARI12619.pdf": {
        "source_id": "PLAT-DOC-ML-006",
        "title": "Prognostics and Health Management Analytics for Industrial Assets",
        "source_type": "Journal Paper",
        "authority_level": "A",
        "owner": "JOBARI PHM"
    },
    "ilide.info-mc4301-ml-unit-2-model-evaluation-and-feature-engineering-pr_9c18eb7d1471cb9f7ac0fed4b6f50be0.pdf": {
        "source_id": "PLAT-DOC-ML-007",
        "title": "ML Model Evaluation Patterns and Feature Engineering Principles",
        "source_type": "Technical Guide",
        "authority_level": "A",
        "owner": "ML Education"
    },
    "rsta.2020.0209.pdf": {
        "source_id": "PLAT-DOC-ML-008",
        "title": "Royal Society Philosophical Transactions on Asset Health Monitoring",
        "source_type": "Royal Society Journal Paper",
        "authority_level": "A",
        "owner": "Royal Society"
    },
    "survey.pdf": {
        "source_id": "PLAT-DOC-ML-009",
        "title": "Time-Series Analytics and Anomaly Detection Methodology Survey",
        "source_type": "Academic Survey",
        "authority_level": "A",
        "owner": "ML Analytics"
    },
    "L-0013405598-pdf.pdf": {
        "source_id": "PLAT-DOC-ML-010",
        "title": "Applied Machine Learning Systems Reference Manual",
        "source_type": "Technical Reference",
        "authority_level": "A",
        "owner": "Industrial ML"
    }
}


def compute_sha256(filepath: str) -> str:
    """Computes SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def run_phase_0_harvester():
    logger.info("=== Starting Sprint 3 Phase 0 Harvester & Source Register ===")

    os.makedirs(RAW_DOCS_DIR, exist_ok=True)

    # 1. Load existing Source Register
    existing_register = []
    if os.path.exists(SOURCE_REGISTER_FILE):
        with open(SOURCE_REGISTER_FILE, "r", encoding="utf-8") as f:
            existing_register = json.load(f)

    reg_map = {item["source_id"]: item for item in existing_register}

    manifest_entries = []
    registered_count = 0

    # 2. Iterate over ML-knowledge-graph files
    for filename, meta in ML_CORPUS_MAP.items():
        src_path = os.path.join(SOURCE_DIR, filename)
        if not os.path.exists(src_path):
            logger.warning(f"File not found in ML-knowledge-graph: {filename}")
            continue

        # Copy to raw_documents/ml_methodology/
        dest_path = os.path.join(RAW_DOCS_DIR, filename)
        shutil.copy2(src_path, dest_path)

        file_size = os.path.getsize(dest_path)
        sha256 = compute_sha256(dest_path)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Build Source Register Record
        source_record = {
            "source_id": meta["source_id"],
            "title": meta["title"],
            "knowledge_domain": "ml_methodology",
            "source_type": meta["source_type"],
            "source_location": f"aiconnex_knowledge/06_raw_documents/ml_methodology/{filename}",
            "authority_level": meta["authority_level"],
            "owner": meta["owner"],
            "tenant_scope": "global",
            "license": "Technical Reference",
            "version": "1.0",
            "status": "Approved",
            "approved_at": now_iso
        }

        reg_map[meta["source_id"]] = source_record
        registered_count += 1

        manifest_entries.append({
            "source_id": meta["source_id"],
            "filename": filename,
            "size_bytes": file_size,
            "sha256_hash": sha256,
            "registered_at": now_iso
        })

    # Save updated Source Register
    updated_register = list(reg_map.values())
    with open(SOURCE_REGISTER_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_register, f, indent=2)

    logger.info(f"Updated Source Register ({SOURCE_REGISTER_FILE}) with {registered_count} ML methodology sources.")

    # Save Manifest Audit Log
    manifest = {
        "manifest_type": "ML_Methodology_Raw_Manifest",
        "version": "1.0",
        "total_sources": len(manifest_entries),
        "sources": manifest_entries
    }
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Generated ML Source Manifest at {MANIFEST_FILE}")
    logger.info("=== Phase 0 Harvester & Source Register Complete! ===")


if __name__ == "__main__":
    run_phase_0_harvester()
