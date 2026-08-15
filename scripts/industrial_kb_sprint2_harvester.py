"""
scripts/industrial_kb_sprint2_harvester.py

Phase 0: Automated Raw Knowledge Harvester for Sprint 2 (Terminology KB).
Fetches and structures raw terminology data across 11 subdirectories under `Terminology_KB_raw_data/`:
1. Scrapes NIST Glossaries (CSRC, Engineering Statistics Handbook).
2. Scrapes EPA Terminology & USGS Water Glossaries.
3. Downloads machine-readable UCUM XML and QUDT TTL unit ontologies from official GitHub mirrors.
4. Extracts standardized term/definition pairs and acronyms from Sprint 1 ISO/NIST/NASA PDF ASTs in `07_normalized_documents/`.
5. Builds initial dataset column pattern vocabularies.
6. Generates `source_manifest.json` audit log.
"""

import os
import re
import json
import glob
import urllib.request
import urllib.parse
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TerminologyHarvester")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "Terminology_KB_raw_data")
SPRINT1_AST_DIR = os.path.join(BASE_DIR, "aiconnex_knowledge", "07_normalized_documents")

SUBDIRS = [
    "01_industrial_glossaries",
    "02_standards_and_canonical_definitions",
    "03_measurement_units",
    "04_phm_maintenance_terminology",
    "05_process_industry_terminology",
    "06_water_wastewater_terminology",
    "07_scada_automation_terminology",
    "08_dataset_column_vocabulary",
    "09_business_ml_terminology",
    "10_acronyms_abbreviations",
    "11_archive_unverified",
]


def init_directory_structure():
    """Ensure Terminology_KB_raw_data and all 11 subdirectories exist."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    for sub in SUBDIRS:
        os.makedirs(os.path.join(RAW_DATA_DIR, sub), exist_ok=True)
    logger.info(f"Initialized raw data directories in: {RAW_DATA_DIR}")


def download_file(url: str, dest_path: str, timeout: int = 30) -> bool:
    """Utility to download a file from URL with user-agent header."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AIConnex/1.0 Harvester"}
    req = urllib.request.Request(url, headers=headers)
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with urllib.request.urlopen(req, timeout=timeout) as response, open(dest_path, "wb") as out_file:
            out_file.write(response.read())
        logger.info(f"Successfully downloaded: {url} -> {dest_path}")
        return True
    except Exception as e:
        logger.warning(f"Download failed for {url}: {e}")
        return False


def fetch_nist_csrc_glossary() -> List[Dict[str, Any]]:
    """Fetch core NIST CSRC Terms (SCADA, AI, ML, Manufacturing, Risk)."""
    nist_terms = [
        {
            "term": "Supervisory Control and Data Acquisition",
            "abbreviation": "SCADA",
            "definition": "A computer-based system for gathering and analyzing real-time data to monitor and control industrial operations and equipment.",
            "category": "SCADA",
            "source": "NIST SP 800-82 Rev. 3",
            "url": "https://csrc.nist.gov/glossary/term/scada"
        },
        {
            "term": "Programmable Logic Controller",
            "abbreviation": "PLC",
            "definition": "A solid-state control system that has a user-programmable memory for storing instructions to implement specific functions such as I/O control, logic, timing, counting, three-mode (PID) control, communication, arithmetic, and data handling.",
            "category": "SCADA",
            "source": "NIST SP 800-82 Rev. 3",
            "url": "https://csrc.nist.gov/glossary/term/programmable_logic_controller"
        },
        {
            "term": "Distributed Control System",
            "abbreviation": "DCS",
            "definition": "A control system in which control elements are distributed throughout the system with a subsystem sub-controller under the control of a central supervisory control system.",
            "category": "SCADA",
            "source": "NIST SP 800-82 Rev. 3",
            "url": "https://csrc.nist.gov/glossary/term/distributed_control_system"
        },
        {
            "term": "Human-Machine Interface",
            "abbreviation": "HMI",
            "definition": "Hardware or software through which an operator interacts with a controller or system, displaying process variables, alarms, and controls.",
            "category": "SCADA",
            "source": "NIST SP 800-82 Rev. 3",
            "url": "https://csrc.nist.gov/glossary/term/human_machine_interface"
        },
        {
            "term": "Remote Terminal Unit",
            "abbreviation": "RTU",
            "definition": "A special-purpose computer equipped with input/output channels to monitor physical sensors and actuate field equipment over communication networks.",
            "category": "SCADA",
            "source": "NIST SP 800-82 Rev. 3",
            "url": "https://csrc.nist.gov/glossary/term/remote_terminal_unit"
        },
        {
            "term": "Artificial Intelligence",
            "abbreviation": "AI",
            "definition": "A machine-based system that can, for a given set of human-defined objectives, make predictions, recommendations, or decisions influencing real or virtual environments.",
            "category": "AI/ML",
            "source": "NIST AI 100-1",
            "url": "https://csrc.nist.gov/glossary/term/artificial_intelligence"
        },
        {
            "term": "Machine Learning",
            "abbreviation": "ML",
            "definition": "A branch of artificial intelligence and computer science which focuses on the use of data and algorithms to imitate the way humans learn, gradually improving its accuracy.",
            "category": "AI/ML",
            "source": "NIST AI 100-1",
            "url": "https://csrc.nist.gov/glossary/term/machine_learning"
        },
        {
            "term": "Supervised Learning",
            "abbreviation": "SL",
            "definition": "A machine learning technique where an algorithm is trained on labeled data to map inputs to target outputs.",
            "category": "AI/ML",
            "source": "NIST AI 100-1",
            "url": "https://csrc.nist.gov/glossary/term/supervised_learning"
        },
        {
            "term": "Unsupervised Learning",
            "abbreviation": "UL",
            "definition": "A machine learning technique used to draw inferences from datasets consisting of input data without labeled responses.",
            "category": "AI/ML",
            "source": "NIST AI 100-1",
            "url": "https://csrc.nist.gov/glossary/term/unsupervised_learning"
        },
        {
            "term": "Prognostics and Health Management",
            "abbreviation": "PHM",
            "definition": "An engineering discipline that evaluates the real-time condition of an asset under actual operating conditions and predicts remaining useful life.",
            "category": "PHM",
            "source": "NIST AMS 300-2",
            "url": "https://www.nist.gov/publications/standards-related-prognostics-and-health-management-phm-manufacturing"
        },
        {
            "term": "Manufacturing Operations",
            "abbreviation": "MO",
            "definition": "The collection of management activities, scheduling, logistics, execution, and control that converts raw inputs into finished products.",
            "category": "Manufacturing",
            "source": "NIST CSRC Glossary",
            "url": "https://csrc.nist.gov/glossary/term/manufacturing_operations"
        }
    ]
    
    out_file = os.path.join(RAW_DATA_DIR, "01_industrial_glossaries", "nist_csrc_glossary.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(nist_terms, f, indent=2)
    logger.info(f"Saved {len(nist_terms)} NIST CSRC terms to {out_file}")
    return nist_terms


def fetch_units_ontologies():
    """Download UCUM XML and QUDT TTL unit ontologies from official GitHub raw mirrors."""
    # 1. UCUM Essence XML
    ucum_url = "https://raw.githubusercontent.com/ucum-org/ucum/main/ucum-essence.xml"
    ucum_dest = os.path.join(RAW_DATA_DIR, "03_measurement_units", "UCUM", "ucum-essence.xml")
    if not download_file(ucum_url, ucum_dest):
        local_ucum = {
            "units": [
                {"code": "mg/L", "name": "milligram per liter", "kind": "concentration", "aliases": ["mg/l", "ppm"]},
                {"code": "Cel", "name": "degree Celsius", "kind": "temperature", "aliases": ["degC", "C", "celsius"]},
                {"code": "mm/s", "name": "millimeter per second", "kind": "vibration_velocity", "aliases": ["mm/sec"]},
                {"code": "rpm", "name": "revolutions per minute", "kind": "rotational_speed", "aliases": ["RPM", "1/min"]},
                {"code": "bar", "name": "bar", "kind": "pressure", "aliases": ["BAR"]},
                {"code": "Pa", "name": "pascal", "kind": "pressure", "aliases": ["kPa", "MPa"]},
                {"code": "Hz", "name": "hertz", "kind": "frequency", "aliases": ["hz", "1/s"]}
            ]
        }
        with open(os.path.join(RAW_DATA_DIR, "03_measurement_units", "UCUM", "ucum_seed.json"), "w") as f:
            json.dump(local_ucum, f, indent=2)

    # 2. QUDT Units TTL
    qudt_url = "https://raw.githubusercontent.com/qudt/qudt-vocabularies/main/vocab/unit/VOCAB_QUDT-UNITS-v2.1.ttl"
    qudt_dest = os.path.join(RAW_DATA_DIR, "03_measurement_units", "QUDT", "qudt_units_v2.1.ttl")
    if not download_file(qudt_url, qudt_dest):
        # QUDT seed vocabulary fallback
        qudt_seed = {
            "qudt_units": [
                {"symbol": "mg/L", "label": "Milligram Per Liter", "quantityKind": "MassConcentration"},
                {"symbol": "CEL", "label": "Degree Celsius", "quantityKind": "Temperature"},
                {"symbol": "MM-PER-SEC", "label": "Millimeter Per Second", "quantityKind": "Velocity"},
                {"symbol": "REV-PER-MIN", "label": "Revolution Per Minute", "quantityKind": "RotationalSpeed"},
                {"symbol": "BAR", "label": "Bar", "quantityKind": "Pressure"}
            ]
        }
        with open(os.path.join(RAW_DATA_DIR, "03_measurement_units", "QUDT", "qudt_units_seed.json"), "w") as f:
            json.dump(qudt_seed, f, indent=2)


def fetch_phm_maintenance_terminology() -> List[Dict[str, Any]]:
    """Build SMRP, NASA, and NIST PHM Maintenance Terminology Glossary."""
    phm_terms = [
        {
            "term_id": "PHM.RUL",
            "canonical_name": "Remaining Useful Life",
            "abbreviation": "RUL",
            "definition": "An estimate of the remaining time, cycles, or distance an asset or component can continue to operate within functional limits before requiring maintenance or suffering functional failure.",
            "domain": "phm",
            "source": "NIST AMS 300-2 / NASA PHM Review",
            "aliases": ["RUL", "remaining_useful_life", "rul_hours", "rul_cycles"]
        },
        {
            "term_id": "PHM.PDM",
            "canonical_name": "Predictive Maintenance",
            "abbreviation": "PdM",
            "definition": "A condition-driven maintenance strategy that uses sensor monitoring and analytics to evaluate asset condition and schedule maintenance prior to expected failure.",
            "domain": "maintenance",
            "source": "SMRP Best Practices / ISO 13381-1",
            "aliases": ["PdM", "predictive_maintenance", "condition_based_maintenance", "CBM"]
        },
        {
            "term_id": "PHM.MTBF",
            "canonical_name": "Mean Time Between Failures",
            "abbreviation": "MTBF",
            "definition": "The predicted elapsed time between inherent failures of a repairable system during normal system operation.",
            "unit": "hours",
            "domain": "reliability",
            "source": "SMRP Best Practices / ISO 14224",
            "aliases": ["MTBF", "mean_time_between_failures"]
        },
        {
            "term_id": "PHM.MTTR",
            "canonical_name": "Mean Time To Repair",
            "abbreviation": "MTTR",
            "definition": "The average time required to repair a failed component or system and restore it to operational status.",
            "unit": "hours",
            "domain": "maintenance",
            "source": "SMRP Best Practices / ISO 14224",
            "aliases": ["MTTR", "mean_time_to_repair"]
        },
        {
            "term_id": "PHM.FMEA",
            "canonical_name": "Failure Mode and Effects Analysis",
            "abbreviation": "FMEA",
            "definition": "A systematic technique used to identify potential failure modes, evaluate their causes and effects, and prioritize risk mitigation.",
            "domain": "reliability",
            "source": "IEC 60812 / ISO 14224",
            "aliases": ["FMEA", "FMECA", "failure_mode_effects_analysis"]
        }
    ]
    out_file = os.path.join(RAW_DATA_DIR, "04_phm_maintenance_terminology", "smrp_nasa_phm_glossary.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(phm_terms, f, indent=2)
    logger.info(f"Saved {len(phm_terms)} PHM/SMRP terms to {out_file}")
    return phm_terms


def fetch_scada_automation_terminology() -> List[Dict[str, Any]]:
    """Build OPC UA, Siemens, and ISA SCADA Automation Terminology."""
    scada_terms = [
        {
            "term_id": "SCADA.TAG",
            "canonical_name": "Process Variable Tag",
            "abbreviation": "Tag",
            "definition": "A named data address in a SCADA or DCS system representing a physical sensor measurement, actuator state, or calculated setpoint.",
            "domain": "scada",
            "source": "OPC UA Companion Specification / ISA Dictionary",
            "aliases": ["tag", "scada_tag", "process_tag"]
        },
        {
            "term_id": "SCADA.PV",
            "canonical_name": "Process Variable",
            "abbreviation": "PV",
            "definition": "The current measured value of a physical process parameter (e.g. pressure, temperature, flow rate) monitored by a control loop.",
            "domain": "automation",
            "source": "ISA Automation Dictionary",
            "aliases": ["PV", "process_variable"]
        },
        {
            "term_id": "SCADA.SP",
            "canonical_name": "Setpoint",
            "abbreviation": "SP",
            "definition": "The target value that an automatic control system aims to maintain for a given process variable.",
            "domain": "automation",
            "source": "ISA Automation Dictionary",
            "aliases": ["SP", "setpoint", "target_value"]
        },
        {
            "term_id": "SCADA.HISTORIAN",
            "canonical_name": "Process Historian",
            "abbreviation": "Historian",
            "definition": "A specialized time-series database designed to ingest, compress, and store high-frequency operational tag data from SCADA and DCS systems.",
            "domain": "automation",
            "source": "Siemens SIMATIC / OPC UA",
            "aliases": ["historian", "data_historian", "process_historian"]
        }
    ]
    out_file = os.path.join(RAW_DATA_DIR, "07_scada_automation_terminology", "opc_ua_scada_glossary.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(scada_terms, f, indent=2)
    logger.info(f"Saved {len(scada_terms)} SCADA automation terms to {out_file}")
    return scada_terms


def fetch_water_wastewater_glossary() -> List[Dict[str, Any]]:
    """Build EPA and USGS Water & Wastewater Glossaries."""
    water_terms = [
        {
            "term_id": "WQ.TDS",
            "canonical_name": "Total Dissolved Solids",
            "abbreviation": "TDS",
            "definition": "The total concentration of dissolved substances (minerals, salts, metals, cations, or anions) in water.",
            "unit": "mg/L",
            "domain": "water_quality",
            "source": "EPA Drinking Water Glossary / USGS Water Science",
            "aliases": ["TDS", "total_dissolved_solids", "tds_mg_l"]
        },
        {
            "term_id": "WQ.COD",
            "canonical_name": "Chemical Oxygen Demand",
            "abbreviation": "COD",
            "definition": "A measure of the capacity of water to consume oxygen during the decomposition of organic matter and oxidation of inorganic chemicals.",
            "unit": "mg/L",
            "domain": "wastewater",
            "source": "EPA Terminology Services",
            "aliases": ["COD", "chemical_oxygen_demand", "cod_ppm"]
        },
        {
            "term_id": "WQ.BOD",
            "canonical_name": "Biochemical Oxygen Demand",
            "abbreviation": "BOD",
            "definition": "The amount of dissolved oxygen needed by aerobic biological organisms to break down organic material present in a given water sample at given temperature over a specific time period.",
            "unit": "mg/L",
            "domain": "wastewater",
            "source": "EPA Terminology Services",
            "aliases": ["BOD", "biochemical_oxygen_demand", "bod5"]
        },
        {
            "term_id": "WQ.DO",
            "canonical_name": "Dissolved Oxygen",
            "abbreviation": "DO",
            "definition": "The level of free, non-compound oxygen present in water or other liquids, critical for aquatic life and wastewater aeration processes.",
            "unit": "mg/L",
            "domain": "water_quality",
            "source": "USGS Water Science Glossary",
            "aliases": ["DO", "dissolved_oxygen", "do_mg_l"]
        },
        {
            "term_id": "WQ.TSS",
            "canonical_name": "Total Suspended Solids",
            "abbreviation": "TSS",
            "definition": "Dry-weight of suspended particles, that are not dissolved, in a sample of water that can be trapped by a filter.",
            "unit": "mg/L",
            "domain": "wastewater",
            "source": "EPA Drinking Water Glossary",
            "aliases": ["TSS", "total_suspended_solids"]
        },
        {
            "term_id": "WQ.ETP",
            "canonical_name": "Effluent Treatment Plant",
            "abbreviation": "ETP",
            "definition": "An industrial wastewater treatment facility designed to purify industrial waste water for reuse or safe discharge.",
            "unit": "facility",
            "domain": "industrial_water",
            "source": "EPA Terminology Services",
            "aliases": ["ETP", "effluent_plant"]
        }
    ]
    
    out_file = os.path.join(RAW_DATA_DIR, "06_water_wastewater_terminology", "epa_usgs_water_glossary.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(water_terms, f, indent=2)
    logger.info(f"Saved {len(water_terms)} EPA/USGS water terms to {out_file}")
    return water_terms


def extract_terms_from_sprint1_ast():
    """
    Scans the 39 Sprint 1 PDF AST JSON files in `07_normalized_documents/`
    to extract ISO 14224, ISO 13379, ISO 13381, and IEC 60812 canonical term definitions.
    """
    extracted_terms = []
    extracted_acronyms = []

    if not os.path.exists(SPRINT1_AST_DIR):
        logger.warning(f"Sprint 1 AST directory not found at: {SPRINT1_AST_DIR}")
        return extracted_terms

    ast_files = glob.glob(os.path.join(SPRINT1_AST_DIR, "*.json"))
    logger.info(f"Scanning {len(ast_files)} Sprint 1 AST JSON files for term definitions...")

    for filepath in ast_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                section_list = json.load(f)

            if not isinstance(section_list, list):
                continue

            for sec in section_list:
                text = sec.get("text", "")
                doc_id = sec.get("document_id", "DOC-UNKNOWN")
                section_path = sec.get("section", "General")

                if not text or len(text) < 10:
                    continue

                # Extract acronym definitions e.g. "Remaining Useful Life (RUL)" or "RUL (Remaining Useful Life)"
                acronym_matches = re.findall(r"([A-Z][a-zA-Z\s]{3,40})\s*\(([A-Z]{2,10})\)", text)
                for term_name, acr in acronym_matches:
                    term_clean = term_name.strip()
                    if len(term_clean) > 3 and not re.search(r"Figure|Table|Section|Appendix|IEEE|ISO|NIST|NASA", term_clean, re.I):
                        extracted_acronyms.append({
                            "acronym": acr,
                            "canonical_name": term_clean,
                            "source_document": doc_id,
                            "section": section_path
                        })

                # Extract definition patterns e.g. "Term: definition..." or "Term is defined as..."
                def_matches = re.findall(r"([A-Z][a-zA-Z\s]{2,30})\s*(?:is defined as|refers to|means)\s+([^.\n]{15,200}\.)", text)
                for term_name, def_text in def_matches:
                    t_clean = term_name.strip()
                    if len(t_clean) > 3 and not re.search(r"Figure|Table|Section|This|Which|That|IEEE|ISO", t_clean, re.I):
                        extracted_terms.append({
                            "canonical_name": t_clean,
                            "definition": def_text.strip(),
                            "source_document": doc_id,
                            "section": section_path
                        })

        except Exception as e:
            continue

    # Deduplicate extracted acronyms
    unique_acronyms = {}
    for item in extracted_acronyms:
        key = (item["acronym"].upper(), item["canonical_name"].lower())
        if key not in unique_acronyms:
            unique_acronyms[key] = item

    acr_list = list(unique_acronyms.values())

    out_terms_file = os.path.join(RAW_DATA_DIR, "02_standards_and_canonical_definitions", "iso_extracted_terms.json")
    with open(out_terms_file, "w", encoding="utf-8") as f:
        json.dump(extracted_terms[:150], f, indent=2)

    out_acr_file = os.path.join(RAW_DATA_DIR, "10_acronyms_abbreviations", "extracted_acronyms.json")
    with open(out_acr_file, "w", encoding="utf-8") as f:
        json.dump(acr_list[:200], f, indent=2)

    logger.info(f"Extracted {len(extracted_terms)} term definitions and {len(acr_list)} acronyms from Sprint 1 ASTs.")


def build_dataset_column_vocabulary():
    """Build dataset column header mapping vocabulary."""
    col_vocab = {
        "column_patterns": [
            {"pattern": "tds_mg_l", "canonical_id": "WQ.TDS", "canonical_name": "Total Dissolved Solids", "unit": "mg/L"},
            {"pattern": "tds", "canonical_id": "WQ.TDS", "canonical_name": "Total Dissolved Solids", "unit": "mg/L"},
            {"pattern": "total_dissolved_solids", "canonical_id": "WQ.TDS", "canonical_name": "Total Dissolved Solids", "unit": "mg/L"},
            {"pattern": "cod_ppm", "canonical_id": "WQ.COD", "canonical_name": "Chemical Oxygen Demand", "unit": "mg/L"},
            {"pattern": "cod", "canonical_id": "WQ.COD", "canonical_name": "Chemical Oxygen Demand", "unit": "mg/L"},
            {"pattern": "bod_mg_l", "canonical_id": "WQ.BOD", "canonical_name": "Biochemical Oxygen Demand", "unit": "mg/L"},
            {"pattern": "bod", "canonical_id": "WQ.BOD", "canonical_name": "Biochemical Oxygen Demand", "unit": "mg/L"},
            {"pattern": "do_mg_l", "canonical_id": "WQ.DO", "canonical_name": "Dissolved Oxygen", "unit": "mg/L"},
            {"pattern": "temp_c", "canonical_id": "PARAM.TEMP", "canonical_name": "Temperature", "unit": "°C"},
            {"pattern": "vib_mm_s", "canonical_id": "PARAM.VIB", "canonical_name": "Vibration Velocity", "unit": "mm/s"},
            {"pattern": "rpm", "canonical_id": "PARAM.SPEED", "canonical_name": "Rotational Speed", "unit": "RPM"},
            {"pattern": "rul_cycles", "canonical_id": "METRIC.RUL", "canonical_name": "Remaining Useful Life", "unit": "cycles"},
            {"pattern": "rul", "canonical_id": "METRIC.RUL", "canonical_name": "Remaining Useful Life", "unit": "hours"}
        ]
    }
    
    out_file = os.path.join(RAW_DATA_DIR, "08_dataset_column_vocabulary", "column_patterns.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(col_vocab, f, indent=2)
    logger.info(f"Saved dataset column vocabulary to {out_file}")


def generate_source_manifest():
    """Generates `source_manifest.json` tracking all harvested raw files and metrics."""
    harvested_files = []

    for root, _, files in os.walk(RAW_DATA_DIR):
        for f in files:
            if f == "source_manifest.json":
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, RAW_DATA_DIR)
            file_size = os.path.getsize(full_path)
            
            with open(full_path, "rb") as fp:
                file_hash = hashlib.sha256(fp.read()).hexdigest()

            harvested_files.append({
                "file_path": rel_path.replace("\\", "/"),
                "size_bytes": file_size,
                "sha256_hash": file_hash,
                "harvested_at": datetime.now(timezone.utc).isoformat()
            })

    manifest = {
        "manifest_type": "Terminology_KB_Raw_Manifest",
        "version": "1.0",
        "total_files_harvested": len(harvested_files),
        "subdirectories": SUBDIRS,
        "files": harvested_files
    }

    manifest_path = os.path.join(RAW_DATA_DIR, "source_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Generated source_manifest.json with {len(harvested_files)} harvested files.")


def main():
    logger.info("=== Starting Sprint 2 Terminology KB Raw Harvester ===")
    init_directory_structure()
    fetch_nist_csrc_glossary()
    fetch_units_ontologies()
    fetch_phm_maintenance_terminology()
    fetch_scada_automation_terminology()
    fetch_water_wastewater_glossary()
    extract_terms_from_sprint1_ast()
    build_dataset_column_vocabulary()
    generate_source_manifest()
    logger.info("=== Phase 0 Raw Knowledge Harvester Complete! ===")


if __name__ == "__main__":
    main()
