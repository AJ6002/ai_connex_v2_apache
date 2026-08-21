# AI-ConneX Production Migration Cleanup Report

**Report Date:** August 21, 2026  
**Target Repository:** `ai_connex_v2_apache`  
**Classification:** Migration Artifact & Infrastructure Audit Report  

---

## 1. Removed Artifacts / Cleanup Plan

| Path | Reason | Evidence | Status |
|---|---|---|---|
| `scratch/run_graphify.py` | Temporary graphify script created during visualization generation | One-off helper script | **Marked for Cleanup** |
| `scratch/generate_graphify.py` | Temporary graphify script created during visualization generation | One-off helper script | **Marked for Cleanup** |
| `archive_legacy/services/sagemaker_pipeline` | Obsolete AWS SageMaker pipeline files incompatible with Apache-first target architecture | AWS SageMaker lock-in | **Marked for Drop** |
| `archive_legacy/.mem0_qdrant` | Obsolete v1 vector database cache | Outdated embeddings | **Marked for Drop** |

---

## 2. Replaced Infrastructure & Integration Components

| Old Component | New Apache Component | Reason | Status |
|---|---|---|---|
| **Flask Monolithic Microservices (MS1-MS9)** | **FastAPI Async Ingestion API & Pydantic Contracts** | Replaced Flask HTTP servers with async FastAPI gateway (`data-studio/intake/app.py`) and 18 typed contracts (`contracts/`). | **Replaced** |
| **Local Machine Execution** | **Isolated Docker Sandbox (`DockerJobManager`)** | Replaced root local python execution with non-root, network-disabled containers (`--network none`). | **Replaced** |
| **Pandas Dataframe Intermediate Pipelines** | **PyArrow & Apache DataFusion Columnar Engine** | Replaced in-memory Pandas dataframe operations with PyArrow IPC and Parquet datasets. | **Replaced** |
| **Manual Local Docker Builds** | **GitHub Actions CI/CD with Trivy Security & GHCR** | Replaced unverified local builds with automated Trivy scans and GHCR container publishing (`ghcr.io/aj6002/ai_connex_v2_apache/aiconnex-base:latest`). | **Replaced** |

---

## 3. Preserved Domain Logic & Assets

| Component | Why Preserved | Location |
|---|---|---|
| **ISO Vibration Primitives** | Physical sensor mathematics and ISO 10816 formulas | `registries/math_physics/primitives.json` |
| **Industrial Vocabulary Glossary** | Domain unit definitions and sensor taxonomies | `registries/industrial_vocabulary/glossary.json` |
| **17-View Presentation Components** | Fully functional React 19 UI shell | `frontend/src/components/` |
| **Raw Domain Knowledge Documents** | Turbofan predictive maintenance & equipment specs | `knowledge/` |
| **Leakage-Free Time-Series Split Algorithms** | Valuable temporal data split algorithms | `archive_legacy/services/6_split/` -> Target: `ml-studio/split/` |
| **Feature Engineering Primitives** | Rolling window, lag, and FFT spectral features | `archive_legacy/services/5_feature_engineering/` -> Target: `ml-studio/feature-engineering/` |

---

## 4. Uncertain / Items Kept for Reference

| Path | Why Uncertain | Recommended Action |
|---|---|---|
| `archive_legacy/services/1_dataset_profiler` through `9_deploy_monitor` | Contains valuable domain algorithms mixed with obsolete Flask infrastructure | **KEEP IN `archive_legacy/` (IGNORED IN GIT)** until domain logic porting to `ml-studio/` is complete. |

---

## 5. Remaining Legacy References Check

| Reference Pattern | Search Scope | Findings | Action Taken |
|---|---|---|---|
| `old_backend.*` | Active codebase | 0 occurrences | None needed |
| `legacy.*` | Active codebase | 0 occurrences | None needed |
| `backend_old.*` | Active codebase | 0 occurrences | None needed |
| `archive_legacy` | `contracts/`, `data-studio/`, `frontend/`, `tests/` | 0 active code imports | Confirmed isolated in documentation & `.gitignore` |

---

## 6. Validation & Build Verification

- [x] **Pytest Contract Unit Tests**: 7/7 passing 100% green (`tests/contracts/test_contracts.py`).
- [x] **React 19 / Vite 6 Production Build**: Clean compilation (`frontend/`).
- [x] **Docker Build Verification**: Baseline container image built and loaded cleanly.
- [x] **GitHub Actions CI/CD**: 4-stage workflow 100% green on `main` branch.
- [x] **Git Cleanliness**: `graphify-out/`, `scratch/`, and `archive_legacy/` fully excluded in `.gitignore`.
