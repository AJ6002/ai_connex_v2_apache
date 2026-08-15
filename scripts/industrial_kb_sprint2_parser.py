"""
scripts/industrial_kb_sprint2_parser.py

Phase 1: Canonical Term Parser and Registry Compiler for Sprint 2 (Terminology KB).
Reads harvested raw terminology data from `Terminology_KB_raw_data/` and compiles
4 structured YAML registries under `aiconnex_knowledge/05_terminology/`:
1. `canonical_terms.yaml`: Master catalog of canonical terms, definitions, domains, and typed relations.
2. `synonyms.yaml`: Synonym & abbreviation lookup map distinguishing exact synonyms from related concepts.
3. `column_mappings.yaml`: Pre-configured dataset column pattern mappings.
4. `units_vocabulary.yaml`: Standardized units, symbols, UCUM codes, and aliases.
"""

import os
import re
import json
import yaml
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TerminologyParser")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "Terminology_KB_raw_data")
OUTPUT_TERMINOLOGY_DIR = os.path.join(BASE_DIR, "aiconnex_knowledge", "05_terminology")


def init_output_dir():
    """Ensure aiconnex_knowledge/05_terminology exists."""
    os.makedirs(OUTPUT_TERMINOLOGY_DIR, exist_ok=True)
    logger.info(f"Initialized terminology directory: {OUTPUT_TERMINOLOGY_DIR}")


def compile_canonical_terms() -> List[Dict[str, Any]]:
    """Compiles master canonical terms from raw harvested files."""
    canonical_terms = []

    # 1. NIST CSRC Terms
    nist_file = os.path.join(RAW_DATA_DIR, "01_industrial_glossaries", "nist_csrc_glossary.json")
    if os.path.exists(nist_file):
        with open(nist_file, "r", encoding="utf-8") as f:
            nist_data = json.load(f)
            for item in nist_data:
                term_id = f"TERM-{item.get('category', 'IND')}-{item.get('abbreviation', item['term'][:6].upper())}"
                canonical_terms.append({
                    "term_id": term_id,
                    "canonical_name": item["term"],
                    "term_type": "industrial_concept" if item.get("category") in ["SCADA", "Manufacturing", "PHM"] else "business_concept",
                    "definition": item["definition"],
                    "synonyms": [item["term"]],
                    "abbreviations": [item["abbreviation"]] if item.get("abbreviation") else [],
                    "domain": [item.get("category", "industrial").lower()],
                    "source": [item.get("source", "NIST CSRC Glossary")],
                    "authority": "A",
                    "status": "Approved"
                })

    # 2. EPA / USGS Water Terms
    water_file = os.path.join(RAW_DATA_DIR, "06_water_wastewater_terminology", "epa_usgs_water_glossary.json")
    if os.path.exists(water_file):
        with open(water_file, "r", encoding="utf-8") as f:
            water_data = json.load(f)
            for item in water_data:
                canonical_terms.append({
                    "term_id": item["term_id"],
                    "canonical_name": item["canonical_name"],
                    "term_type": "measurement",
                    "definition": item["definition"],
                    "synonyms": item.get("aliases", [item["canonical_name"]]),
                    "abbreviations": [item["abbreviation"]] if item.get("abbreviation") else [],
                    "domain": [item.get("domain", "water_quality")],
                    "unit": {"canonical": item.get("unit", "mg/L")},
                    "column_patterns": item.get("aliases", []),
                    "source": [item.get("source", "EPA/USGS Glossary")],
                    "authority": "A",
                    "status": "Approved"
                })

    # 3. PHM & SCADA Terms
    phm_file = os.path.join(RAW_DATA_DIR, "04_phm_maintenance_terminology", "smrp_nasa_phm_glossary.json")
    if os.path.exists(phm_file):
        with open(phm_file, "r", encoding="utf-8") as f:
            phm_data = json.load(f)
            for item in phm_data:
                canonical_terms.append({
                    "term_id": item["term_id"],
                    "canonical_name": item["canonical_name"],
                    "term_type": "industrial_concept",
                    "definition": item["definition"],
                    "synonyms": item.get("aliases", [item["canonical_name"]]),
                    "abbreviations": [item["abbreviation"]] if item.get("abbreviation") else [],
                    "domain": [item.get("domain", "phm")],
                    "unit": {"canonical": item.get("unit")} if item.get("unit") else None,
                    "column_patterns": item.get("aliases", []),
                    "source": [item.get("source", "SMRP / NASA PHM Glossary")],
                    "authority": "A",
                    "status": "Approved"
                })

    scada_file = os.path.join(RAW_DATA_DIR, "07_scada_automation_terminology", "opc_ua_scada_glossary.json")
    if os.path.exists(scada_file):
        with open(scada_file, "r", encoding="utf-8") as f:
            scada_data = json.load(f)
            for item in scada_data:
                canonical_terms.append({
                    "term_id": item["term_id"],
                    "canonical_name": item["canonical_name"],
                    "term_type": "industrial_concept",
                    "definition": item["definition"],
                    "synonyms": item.get("aliases", [item["canonical_name"]]),
                    "abbreviations": [item["abbreviation"]] if item.get("abbreviation") else [],
                    "domain": [item.get("domain", "scada")],
                    "source": [item.get("source", "OPC UA / ISA Glossary")],
                    "authority": "A",
                    "status": "Approved"
                })

    out_yaml = os.path.join(OUTPUT_TERMINOLOGY_DIR, "canonical_terms.yaml")
    with open(out_yaml, "w", encoding="utf-8") as f:
        yaml.dump({"canonical_terms": canonical_terms}, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Compiled {len(canonical_terms)} canonical terms to {out_yaml}")
    return canonical_terms


def compile_synonyms_dictionary(canonical_terms: List[Dict[str, Any]]):
    """Compiles exact synonym and abbreviation lookup dictionary."""
    synonym_map = {}
    related_map = {}

    for t in canonical_terms:
        t_id = t["term_id"]
        c_name = t["canonical_name"]

        # Register canonical name
        synonym_map[c_name.lower()] = {
            "canonical_term_id": t_id,
            "canonical_name": c_name,
            "match_type": "exact"
        }

        # Register synonyms & acronyms
        for syn in t.get("synonyms", []) + t.get("abbreviations", []):
            if syn and syn.lower() not in synonym_map:
                synonym_map[syn.lower()] = {
                    "canonical_term_id": t_id,
                    "canonical_name": c_name,
                    "match_type": "synonym"
                }

    # Add explicit related-concept entries (e.g. COD vs BOD are related metrics, NOT synonyms)
    related_map = {
        "COD": {
            "canonical_term_id": "WQ.COD",
            "canonical_name": "Chemical Oxygen Demand",
            "related_concepts": [
                {"term_id": "WQ.BOD", "canonical_name": "Biochemical Oxygen Demand", "relationship": "same_domain_as"},
                {"term_id": "WQ.TDS", "canonical_name": "Total Dissolved Solids", "relationship": "same_domain_as"}
            ]
        },
        "BOD": {
            "canonical_term_id": "WQ.BOD",
            "canonical_name": "Biochemical Oxygen Demand",
            "related_concepts": [
                {"term_id": "WQ.COD", "canonical_name": "Chemical Oxygen Demand", "relationship": "same_domain_as"}
            ]
        },
        "RUL": {
            "canonical_term_id": "PHM.RUL",
            "canonical_name": "Remaining Useful Life",
            "related_concepts": [
                {"term_id": "PHM.PDM", "canonical_name": "Predictive Maintenance", "relationship": "used_for"}
            ]
        }
    }

    out_yaml = os.path.join(OUTPUT_TERMINOLOGY_DIR, "synonyms.yaml")
    with open(out_yaml, "w", encoding="utf-8") as f:
        yaml.dump({"synonyms_map": synonym_map, "related_concepts_map": related_map}, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Compiled {len(synonym_map)} synonym lookup entries to {out_yaml}")


def compile_column_mappings():
    """Compiles dataset column pattern library."""
    col_file = os.path.join(RAW_DATA_DIR, "08_dataset_column_vocabulary", "column_patterns.json")
    patterns = []
    if os.path.exists(col_file):
        with open(col_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            patterns = data.get("column_patterns", [])

    out_yaml = os.path.join(OUTPUT_TERMINOLOGY_DIR, "column_mappings.yaml")
    with open(out_yaml, "w", encoding="utf-8") as f:
        yaml.dump({"column_mappings": patterns}, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Compiled {len(patterns)} column pattern mappings to {out_yaml}")


def compile_units_vocabulary():
    """Compiles standardized measurement unit vocabulary."""
    units_vocab = [
        {"symbol": "mg/L", "name": "milligram per liter", "ucum_code": "mg/L", "domain": "water_quality", "aliases": ["mg/l", "ppm", "mg/L"]},
        {"symbol": "°C", "name": "degree Celsius", "ucum_code": "Cel", "domain": "thermal", "aliases": ["degC", "C", "celsius", "temp_c"]},
        {"symbol": "mm/s", "name": "millimeter per second", "ucum_code": "mm/s", "domain": "vibration", "aliases": ["mm/sec", "mm_s"]},
        {"symbol": "RPM", "name": "revolutions per minute", "ucum_code": "rpm", "domain": "rotational", "aliases": ["rpm", "1/min"]},
        {"symbol": "bar", "name": "bar", "ucum_code": "bar", "domain": "pressure", "aliases": ["BAR", "bar_g"]},
        {"symbol": "Pa", "name": "pascal", "ucum_code": "Pa", "domain": "pressure", "aliases": ["kPa", "MPa", "psi"]},
        {"symbol": "Hz", "name": "hertz", "ucum_code": "Hz", "domain": "frequency", "aliases": ["hz", "1/s"]}
    ]

    out_yaml = os.path.join(OUTPUT_TERMINOLOGY_DIR, "units_vocabulary.yaml")
    with open(out_yaml, "w", encoding="utf-8") as f:
        yaml.dump({"units_vocabulary": units_vocab}, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Compiled {len(units_vocab)} unit vocabulary entries to {out_yaml}")


def main():
    logger.info("=== Starting Sprint 2 Canonical Term Parser & Compiler ===")
    init_output_dir()
    canonical_terms = compile_canonical_terms()
    compile_synonyms_dictionary(canonical_terms)
    compile_column_mappings()
    compile_units_vocabulary()
    logger.info("=== Phase 1 Terminology Parser & Compiler Complete! ===")


if __name__ == "__main__":
    main()
