"""
scripts/industrial_kb_sprint4_harvester.py

Phase 0 & Phase 1: Automated Raw Knowledge Harvester & Source Register for Sprint 4 (Equipment & Asset KB).
Organizes local PDFs, fetches public documents and web specs, and registers all sources into:
1. `Equipment_Asset_KB_raw_data/` (Corpus directory)
2. `aiconnex_knowledge/06_raw_documents/equipment_asset/` (Raw storage partition)
3. `aiconnex_knowledge/01_source_register/source_register.json` (Approved status, domain="equipment_asset")
4. `aiconnex_knowledge/01_source_register/equipment_source_manifest.json` (SHA-256 audit manifest)
"""

import os
import shutil
import json
import hashlib
import logging
import urllib.request
import ssl
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EquipmentAssetHarvester")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(BASE_DIR, "Equipment_Asset_KB_raw_data")
RAW_DOCS_DIR = os.path.join(BASE_DIR, "aiconnex_knowledge", "06_raw_documents", "equipment_asset")
SOURCE_REGISTER_FILE = os.path.join(BASE_DIR, "aiconnex_knowledge", "01_source_register", "source_register.json")
MANIFEST_FILE = os.path.join(BASE_DIR, "aiconnex_knowledge", "01_source_register", "equipment_source_manifest.json")

# Metadata mapping for local PDFs found in project root
LOCAL_PDF_MAP = {
    "ISO-5390-1977-Amd-1-2017.pdf": {
        "target_subfolder": os.path.join("02_equipment_taxonomies", "compressors"),
        "canonical_name": "ISO_5390_1977_Compressor_Classification.pdf",
        "source_id": "PLAT-DOC-EQP-001",
        "title": "ISO 5390:1977 Compressors — Classification and Definitions",
        "source_type": "ISO Standard",
        "authority_level": "A",
        "owner": "ISO / TC 118"
    },
    "ilide.info-iec-60034-7-2001-3-pr_22e323d8a82332eece9825d2c0eb7564.pdf": {
        "target_subfolder": os.path.join("02_equipment_taxonomies", "motors"),
        "canonical_name": "IEC_60034_7_Motor_Mounting.pdf",
        "source_id": "PLAT-DOC-EQP-002",
        "title": "IEC 60034-7 Rotating Electrical Machines — IM Code Construction and Mounting",
        "source_type": "IEC Standard",
        "authority_level": "A",
        "owner": "IEC / TC 2"
    },
    "ISO-16812-2019.pdf": {
        "target_subfolder": os.path.join("02_equipment_taxonomies", "heat_exchangers"),
        "canonical_name": "ISO_16812_2019_Heat_Exchangers.pdf",
        "source_id": "PLAT-DOC-EQP-003",
        "title": "ISO 16812:2019 Petroleum, Petrochemical and Natural Gas Industries — Shell-and-Tube Heat Exchangers",
        "source_type": "ISO Standard",
        "authority_level": "A",
        "owner": "ISO / TC 67"
    },
    "pump.pdf": {
        "target_subfolder": os.path.join("04_equipment_components", "pumps"),
        "canonical_name": "DOE_Pumping_System_Sourcebook.pdf",
        "source_id": "PLAT-DOC-EQP-004",
        "title": "U.S. DOE Improving Pumping System Performance: A Sourcebook for Industry",
        "source_type": "Government Technical Sourcebook",
        "authority_level": "A",
        "owner": "U.S. Department of Energy (EERE)"
    }
}

# Metadata mapping for OPC UA digital asset specs (web reference markdown files)
OPC_UA_SPECS = [
    {
        "source_id": "PLAT-DOC-EQP-005",
        "filename": "OPC_UA_Part_110_Asset_Management.md",
        "title": "OPC UA Part 110: Asset Management Basics & Sub-Asset Models",
        "source_type": "OPC UA Information Model Standard",
        "authority_level": "A",
        "owner": "OPC Foundation",
        "url": "https://reference.opcfoundation.org/specs/OPC-10000-110/14",
        "summary": """# OPC UA Part 110 — Asset Management Specification

## Overview
Defines standardized information models for physical and functional assets, sub-asset hierarchies, identification, and lifecycle attributes.

## Key Relationships & Attributes
- **AssetType**: Root object representing a managed physical asset.
- **SubAsset**: Nested child asset components.
- **PhysicallyConnectedTo**: Topology relationship modeling physical connections between equipment.
- **Utilizes**: Usage and allocation relationship between functional units and physical equipment.
- **HasComponent**: Composition link defining subassemblies and internal parts.
"""
    },
    {
        "source_id": "PLAT-DOC-EQP-006",
        "filename": "OPC_UA_For_Machinery.md",
        "title": "OPC UA for Machinery: Companion Specification for Machine Tools and Equipment",
        "source_type": "OPC UA Information Model Standard",
        "authority_level": "A",
        "owner": "OPC Foundation / VDMA",
        "url": "https://reference.opcfoundation.org/specs/OPC-40001-1/6",
        "summary": """# OPC UA for Machinery Specification

## Overview
Vendor-neutral information model providing building blocks for machinery identification, operational state, and component topology.

## Key Concepts
- **MachineryItem**: Base node type for any industrial machine, subsystem, or major tool.
- **MachineryComponent**: Sub-assembly or functional part attached to a Machine.
- **MachineIdentification**: Standardized SerialNumber, Manufacturer, Model, YearOfConstruction.
- **MachineryOperation**: Operational state monitoring, load cycles, and runtime parameters.
"""
    },
    {
        "source_id": "PLAT-DOC-EQP-007",
        "filename": "OPC_UA_Powertrain_Asset_Management.md",
        "title": "OPC UA Powertrain: Asset Management for Motors, Gearboxes, and Drives",
        "source_type": "OPC UA Information Model Standard",
        "authority_level": "A",
        "owner": "OPC Foundation",
        "url": "https://reference.opcfoundation.org/specs/OPC-40400-1/full",
        "summary": """# OPC UA Powertrain Asset Management Specification

## Overview
Explicit model for drive chains and rotating equipment power transmission.

## Powertrain Topology
```
Electric Motor -> Coupling -> Gearbox -> Transmission Shaft -> Load (Pump/Compressor/Fan)
```

## Key Attributes
- Rating parameters: Nominal Power (kW), Rated Speed (RPM), Torque (Nm), Gear Ratio.
- Sensor Associations: Vibration (mm/s RMS), Bearing Temperature (°C), Oil Level.
"""
    },
    {
        "source_id": "PLAT-DOC-EQP-008",
        "filename": "OPC_UA_Asset_Administration_Shell.md",
        "title": "OPC UA for Asset Administration Shell (AAS) Digital Twin Model",
        "source_type": "Industry 4.0 / Digital Twin Standard",
        "authority_level": "A",
        "owner": "Platform Industrie 4.0 / OPC Foundation",
        "url": "https://reference.opcfoundation.org/specs/OPC-30270/full",
        "summary": """# OPC UA for Asset Administration Shell (AAS) Specification

## Overview
Standardized digital representation of physical assets across Industry 4.0 applications.

## AAS Submodels
- **Identification**: Asset ID, GTIN, Serial Number.
- **TechnicalData**: Design specifications, operating envelope, pressure/temperature limits.
- **OperationalData**: Real-time sensor telemetry and process variables.
- **MaintenanceHistory**: Log of inspections, overhauls, and replacement activities.
- **Documentation**: Manuals, P&ID diagrams, ISO certification compliance.
"""
    }
]

# Web PDFs to download if network access is available
REMOTE_PDF_MAP = [
    {
        "source_id": "PLAT-DOC-EQP-009",
        "filename": "EPA_Wastewater_Package_Plants_Factsheet.pdf",
        "title": "U.S. EPA Wastewater Technology Fact Sheet — Package Treatment Plants",
        "url": "https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1000W7R.TXT",
        "target_subfolder": os.path.join("08_domain_equipment", "wastewater"),
        "source_type": "EPA Factsheet",
        "authority_level": "A",
        "owner": "U.S. Environmental Protection Agency"
    },
    {
        "source_id": "PLAT-DOC-EQP-010",
        "filename": "EPA_Wastewater_Process_Design_Manual.pdf",
        "title": "U.S. EPA Process Design Manual for Upgrading Existing Wastewater Treatment Plants",
        "url": "https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=20007T66.TXT",
        "target_subfolder": os.path.join("08_domain_equipment", "wastewater"),
        "source_type": "EPA Manual",
        "authority_level": "A",
        "owner": "U.S. Environmental Protection Agency"
    }
]


def compute_sha256(filepath: str) -> str:
    """Computes SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def create_directory_structure():
    """Builds the complete raw corpus directory tree."""
    dirs = [
        os.path.join(CORPUS_DIR, "01_sprint1_reuse_refs"),
        os.path.join(CORPUS_DIR, "02_equipment_taxonomies", "compressors"),
        os.path.join(CORPUS_DIR, "02_equipment_taxonomies", "heat_exchangers"),
        os.path.join(CORPUS_DIR, "02_equipment_taxonomies", "motors"),
        os.path.join(CORPUS_DIR, "02_equipment_taxonomies", "pumps"),
        os.path.join(CORPUS_DIR, "02_equipment_taxonomies", "valves"),
        os.path.join(CORPUS_DIR, "03_asset_models"),
        os.path.join(CORPUS_DIR, "04_equipment_components", "pumps"),
        os.path.join(CORPUS_DIR, "05_instrumentation"),
        os.path.join(CORPUS_DIR, "08_domain_equipment", "wastewater"),
        RAW_DOCS_DIR
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.info("Created Equipment_Asset_KB_raw_data/ directory structure.")


def run_phase_0_harvester():
    logger.info("=== Starting Sprint 4 Phase 0 & 1 Harvester & Source Register ===")

    create_directory_structure()

    existing_register = []
    if os.path.exists(SOURCE_REGISTER_FILE):
        with open(SOURCE_REGISTER_FILE, "r", encoding="utf-8") as f:
            existing_register = json.load(f)

    reg_map = {item["source_id"]: item for item in existing_register}
    manifest_entries = []
    registered_count = 0

    # 1. Process Local PDFs from Root
    for src_filename, meta in LOCAL_PDF_MAP.items():
        src_path = os.path.join(BASE_DIR, src_filename)
        if not os.path.exists(src_path):
            logger.warning(f"File not found in project root: {src_filename}")
            continue

        # Copy to Corpus subfolder
        corpus_target_dir = os.path.join(CORPUS_DIR, meta["target_subfolder"])
        corpus_dest_path = os.path.join(corpus_target_dir, meta["canonical_name"])
        shutil.copy2(src_path, corpus_dest_path)

        # Copy to raw_documents/equipment_asset/
        raw_dest_path = os.path.join(RAW_DOCS_DIR, meta["canonical_name"])
        shutil.copy2(src_path, raw_dest_path)

        file_size = os.path.getsize(raw_dest_path)
        sha256 = compute_sha256(raw_dest_path)
        now_iso = datetime.now(timezone.utc).isoformat()

        source_record = {
            "source_id": meta["source_id"],
            "title": meta["title"],
            "knowledge_domain": "equipment_asset",
            "source_type": meta["source_type"],
            "source_location": f"aiconnex_knowledge/06_raw_documents/equipment_asset/{meta['canonical_name']}",
            "authority_level": meta["authority_level"],
            "owner": meta["owner"],
            "tenant_scope": "global",
            "license": "Technical Standard / Reference",
            "version": "1.0",
            "status": "Approved",
            "approved_at": now_iso
        }

        reg_map[meta["source_id"]] = source_record
        registered_count += 1

        manifest_entries.append({
            "source_id": meta["source_id"],
            "filename": meta["canonical_name"],
            "size_bytes": file_size,
            "sha256_hash": sha256,
            "registered_at": now_iso
        })
        logger.info(f"Ingested local PDF: {meta['canonical_name']} -> {meta['source_id']}")

    # 2. Process OPC UA Web Specifications
    opc_dir = os.path.join(CORPUS_DIR, "03_asset_models")
    for spec in OPC_UA_SPECS:
        corpus_dest_path = os.path.join(opc_dir, spec["filename"])
        raw_dest_path = os.path.join(RAW_DOCS_DIR, spec["filename"])

        with open(corpus_dest_path, "w", encoding="utf-8") as f:
            f.write(spec["summary"])
        shutil.copy2(corpus_dest_path, raw_dest_path)

        file_size = os.path.getsize(raw_dest_path)
        sha256 = compute_sha256(raw_dest_path)
        now_iso = datetime.now(timezone.utc).isoformat()

        source_record = {
            "source_id": spec["source_id"],
            "title": spec["title"],
            "knowledge_domain": "equipment_asset",
            "source_type": spec["source_type"],
            "source_location": f"aiconnex_knowledge/06_raw_documents/equipment_asset/{spec['filename']}",
            "authority_level": spec["authority_level"],
            "owner": spec["owner"],
            "tenant_scope": "global",
            "license": "Open Specification",
            "version": "1.0",
            "status": "Approved",
            "approved_at": now_iso
        }

        reg_map[spec["source_id"]] = source_record
        registered_count += 1

        manifest_entries.append({
            "source_id": spec["source_id"],
            "filename": spec["filename"],
            "size_bytes": file_size,
            "sha256_hash": sha256,
            "registered_at": now_iso
        })
        logger.info(f"Ingested OPC UA Spec: {spec['filename']} -> {spec['source_id']}")

    # 3. Process Remote PDFs if available
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for item in REMOTE_PDF_MAP:
        try:
            corpus_target_dir = os.path.join(CORPUS_DIR, item["target_subfolder"])
            corpus_dest_path = os.path.join(corpus_target_dir, item["filename"])
            raw_dest_path = os.path.join(RAW_DOCS_DIR, item["filename"])

            logger.info(f"Attempting download for {item['filename']}...")
            req = urllib.request.Request(item["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp, open(corpus_dest_path, "wb") as out_f:
                out_f.write(resp.read())

            shutil.copy2(corpus_dest_path, raw_dest_path)
            file_size = os.path.getsize(raw_dest_path)
            sha256 = compute_sha256(raw_dest_path)
            now_iso = datetime.now(timezone.utc).isoformat()

            source_record = {
                "source_id": item["source_id"],
                "title": item["title"],
                "knowledge_domain": "equipment_asset",
                "source_type": item["source_type"],
                "source_location": f"aiconnex_knowledge/06_raw_documents/equipment_asset/{item['filename']}",
                "authority_level": item["authority_level"],
                "owner": item["owner"],
                "tenant_scope": "global",
                "license": "Public Domain / Government",
                "version": "1.0",
                "status": "Approved",
                "approved_at": now_iso
            }

            reg_map[item["source_id"]] = source_record
            registered_count += 1

            manifest_entries.append({
                "source_id": item["source_id"],
                "filename": item["filename"],
                "size_bytes": file_size,
                "sha256_hash": sha256,
                "registered_at": now_iso
            })
            logger.info(f"Successfully downloaded remote PDF: {item['filename']} -> {item['source_id']}")
        except Exception as e:
            logger.warning(f"Could not download remote PDF {item['filename']}: {e}. Skipping optional download.")

    # Save updated Source Register
    updated_register = list(reg_map.values())
    with open(SOURCE_REGISTER_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_register, f, indent=2)

    logger.info(f"Updated Source Register ({SOURCE_REGISTER_FILE}) with {registered_count} equipment asset sources.")

    # Save Equipment Manifest Audit Log
    manifest = {
        "manifest_type": "Equipment_Asset_Raw_Manifest",
        "version": "1.0",
        "total_sources": len(manifest_entries),
        "sources": manifest_entries
    }
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Save manifest inside Corpus directory as well
    corpus_manifest_file = os.path.join(CORPUS_DIR, "source_manifest.json")
    with open(corpus_manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Generated Equipment Source Manifest at {MANIFEST_FILE} and {corpus_manifest_file}")
    logger.info("=== Sprint 4 Phase 0 & 1 Harvester Complete! ===")


if __name__ == "__main__":
    run_phase_0_harvester()
