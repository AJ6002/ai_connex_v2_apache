# AIConnex — Autonomous Industrial ML Pipeline & Dataset Compiler

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Architecture](https://img.shields.io/badge/architecture-9--Node%20Microservices-orange.svg)](#-architecture-overview)
[![Compiler](https://img.shields.io/badge/compiler-Universal%20ZIP%20Relational-purple.svg)](#-universal-zip-dataset-compiler)

**AIConnex** is an end-to-end, domain-agnostic autonomous Machine Learning pipeline and multi-table dataset compiler engineered specifically for complex industrial sensors, IoT telemetry, predictive maintenance (PdM), prognostics and health management (PHM), digital twins, and industrial SCADA automation.

---

## 🌟 Key Features

- **⚡ Universal Relational ZIP Compiler (`aiconnex_zip_compiler`)**: 4-layer autonomous ingestion engine that discovers multi-table folder structures, performs side-by-side index joins on parallel sensor streams, prevents Cartesian row explosions, and vertically stacks multi-device fleets into ML-ready tables.
- **🔍 9-Node Microservice Architecture**: Decoupled microservice DAG orchestrator spanning Dataset Profiling, Recipe Generation, Data Preparation, Feature Engineering, Splitting, HPO Training, Evaluation, and Drift Deployment Monitoring.
- **📊 Master DAG Mapping (1,993 Algorithm Specifications)**: Dynamic automated mapping across 10 ML domains including Regression, Time-Series Analysis, Anomaly Detection, Clustering, Digital Twins, Reinforcement Learning, NLP, and Computer Vision.
- **🛡️ Zero-Leakage Group-Chronological Splitting**: Enforces strict temporal ordering and asset-level entity grouping for validation splitting—eliminating look-ahead data leakage in industrial time-series models.
- **🎯 Multi-Model Production Deep Search**: Automated hyperparameter optimization (HPO) searching across gradient boosted trees (XGBoost, LightGBM), Random Forest ensembles, regularized linear baselines (Ridge, Lasso), and Isolation Forest anomaly detectors.
- **🔒 Industrial Validation Gates (VG_1 & VG_2)**: Automated quality checks for numerical stability, sensor dropout robustness (+20% noise injection test), and false-alarm-rate (FAR) drift monitoring.

---

## 🏗️ Architecture Overview

The platform operates via a 9-node autonomous cascade:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        AIConnex Industrial 9-Node DAG Cascade                          │
└────────────────────────────────────────────────────────────────────────────────────────┘
  [ Multi-Table Raw ZIP / CSV ]
                │
                ▼
  ┌─────────────────────────────┐   Emits meta1.json
  │ Node 1: Dataset Profiler    │ ───────────────────────┐
  └─────────────┬───────────────┘                        │
                │                                        ▼
                │                            ┌──────────────────────┐
                │                            │ Node 2: DAG Matcher  │
                │                            └──────────┬───────────┘
                │                                       │ Emits meta2.json
                ▼                                       ▼
  ┌─────────────────────────────┐            ┌──────────────────────┐
  │ Node 4: Data Prepare        │ ◄──────────│ Node 3: Recipe Engine│ (meta3.json & manifest)
  └─────────────┬───────────────┘            └──────────────────────┘
                │
                ▼
  ┌─────────────────────────────┐   Chronological Lags (t-1, t-5, t-10)
  │ Node 5: Feature Engineering │ ──► Moving Averages & Rolling Std (w=10)
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐   Strict 70/15/15 Temporal Cut
  │ Node 6: Train/Val/Test Split│ ──► Zero Random Shuffling
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐   Multi-Model Production Deep Search
  │ Node 7: HPO Model Trainer   │ ──► XGBoost, LightGBM, Random Forest, Ridge
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐   VG_1 (Sanity) & VG_2 (Robustness/Noise)
  │ Node 8: Model Evaluator     │ ──► Generates RMSE, MAE, R², Predictions CSV
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐   REST Inference Endpoint (:8001)
  │ Node 9: Deploy & Monitor    │ ──► PSI & Feature Drift Monitoring
  └─────────────────────────────┘
```

---

## 📦 Universal ZIP Dataset Compiler

The `aiconnex_zip_compiler` package ingests unformatted industrial ZIP archives containing multiple subfolders, headerless sensor dumps, or separate physical test runs, and compiles them into clean ML feature matrices:

- **Discovery Layer (`discovery.py`)**: Recursively scans directories, detects text encodings (`utf-8`, `latin-1`), filters documentation files, and extracts folder-level entity attributes.
- **Schema Mapper (`schema_mapper.py`)**: Standardizes column headers into canonical `snake_case`, detects `time`/`timestamp` axes, and assigns semantic types.
- **Relational Joiner (`relational_joiner.py`)**: Performs index-matching joins across parallel sensor channels (`collector_current`, `collector_voltage`, `package_temp`) while guarding against row count explosions ($<5\%$ delta safety threshold).
- **Handoff Layer (`handoff.py`)**: Exports per-group merged tables and vertically concatenates aligned fleet groups into `all_groups_combined.csv`.

---

## 🚀 Quick Start

### 1. Installation & Setup

```bash
# Clone repository
git clone https://github.com/AJ6002/aiconnex_demo.git
cd aiconnex_demo

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Universal ZIP Compiler

To compile any multi-table industrial dataset archive:

```bash
python -m aiconnex_zip_compiler compile path/to/dataset.zip -o workspace_data/compiled_output/
```

### 3. Launch Node 1 Dataset Profiler Service

```bash
python aic/1_dataset_profiler/main.py
```

### 4. Execute End-to-End Pipeline

Run the 9-node pipeline end-to-end on any compiled CSV:

```bash
python aic/run_pipeline.py --dataset workspace_data/igbt_compiled/group_thermal_overstress_aging_with_dc_at_gate_merged.csv --target collector_current
```

---

## 🔬 Benchmark Datasets Validated

| Dataset Domain | Ingest Size | Primary Target | Selected DAG | Best Model | Performance ($R^2$ / RMSE) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NASA C-MAPSS Turbofan** | 61,250 rows × 26 cols | RUL (Cycles to Failure) | `DAG_906` (Time-Series) | LightGBM | $R^2 = 0.7156$ · $\text{RMSE} = 36.84$ |
| **NASA IGBT Power Transistor** | 301,680 rows × 7 cols | `collector_current` | `DAG_906` (Time-Series) | XGBoost | $R^2 = 0.9810$ · $\text{RMSE} = 0.0124\text{ A}$ |
| **NASA Algae Raceway** | 235,842 rows × 17 cols | Biomass `density` | `DAG_906` (Time-Series) | XGBoost | $R^2 = 0.8215$ · $\text{RMSE} = 0.0112\text{ g/L}$ |
| **NASA Milling Tool Wear** | 167 cuts × 44 sensors | Flank Wear `VB` | `DAG_241` (Regression) | Random Forest | $R^2 = 0.4056$ · $\text{MAE} = 0.1360\text{ mm}$ |
| **Solar Generation Fleet** | 68,778 rows × 10 cols | `AC_POWER` | `DAG_906` (Time-Series) | XGBoost | $R^2 = 1.0000$ · $\text{RMSE} = 1.4351\text{ kW}$ |

---

## 🛠️ Project Structure

```
aiconnex_demo/
├── aic/                            # AIConnex Microservices Studio
│   ├── 1_dataset_profiler/         # Node 1: FastApi Profiler & Detector
│   ├── 2_dag/                      # Node 2: DAG Orchestrator
│   ├── 3_recipe_orchestrator/      # Node 3: Recipe Generator
│   ├── 4_prepare/                  # Node 4: Data Cleaning & Preprocessing
│   ├── 5_feature_engineering/      # Node 5: Lags, Rolling Windows, Spectral Features
│   ├── 6_split/                    # Node 6: Group-Chronological Splitter
│   ├── 7_train/                    # Node 7: Multi-Model HPO Trainer & Bridge
│   ├── 8_evaluate/                 # Node 8: Validation Gates (VG_1 & VG_2)
│   ├── 9_deploy_monitor/           # Node 9: Model Serving & Drift Detector
│   ├── aiconnex_zip_compiler/      # 4-Layer Universal Relational Dataset Compiler
│   └── run_pipeline.py             # Production CLI Pipeline Runner (1095 lines)
├── aiconnex_ml/                    # Core Industrial Machine Learning Suite
│   ├── regression/                 # Regression Trainers, Losses, Baselines, HPO
│   ├── anomaly/                    # Anomaly Trainers, Thresholding, Operating Modes
│   └── shared/                     # Utilities, Schema Mapping, Quality Checks
├── algorithm_families_complete-2.xlsx # Master DAG Registry (1,993 DAG specifications)
├── workspace_data/                 # Compiled CSVs, Run Manifests, Models, & Scalers
└── README.md                       # Project Documentation
```

---

## 🤖 Chatbot Architecture (`chatbot_5jul`)

The AIConnex Chatbot Rebuild features a single LangGraph conversational agent brain:

- **Single Conversational Brain (`aiconnex_agent`)**: LangGraph StateGraph handles intent gathering (parser node), CUC completion check (`cuc_completion.py`), HITL clarification (`clarification_node.py`), upload advice (`advise_upload_node`), and Scout dataset profiling (`scout_node.py`).
- **`SqliteSaver` Persistence**: Graph state persists to `agent_checkpoints.sqlite` across server auto-reloads and client sessions.
- **`@assistant-ui/react` Integration**: Frontend `ChatView.tsx` streams SSE events (`text`, `interrupt`, `done`) and renders generative UI cards for HITL strategy selection and compiled CSV handoff.
- **Port Mapping**:
  - `3000`: React + Vite frontend (`http://localhost:3000`)
  - `8000`: Flask Agent & Chat backend (`http://localhost:8000`)

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
