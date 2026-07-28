# AIConnex Compiler & Ingestion Architecture v2.0
**Title**: Cooperative Multi-Modal Ingestion, Composable MLOps Nodes, and HITL Governance in Industrial AI Pipelines  
**Status**: Authoritative Architectural Reference (v2.0)  
**Author**: AIConnex Core Engineering & Architecture Team  
**Date**: July 2026  

---

## Executive Summary
In industrial MLOps, datasets are rarely clean, homogeneous CSVs. A single diagnostic package from a solar grid, wind farm, or aerospace test bench often arrives as an archive containing SCADA time series (`.dat`, `.tdms`), relational databases (`.sqlite`), PLC exports (`.xml`), MATLAB structs (`.mat`), calibration spreadsheets (`.xlsx`), and natural language test protocols (`README.txt`, `.pdf`). 

AIConnex Architecture v2.0 represents a paradigm shift from legacy **"Winner-Takes-All" ETL parsers** to a **Cooperative Parser Pipeline powered by an automated Fusion Engine**. Furthermore, v2.0 establishes a strict architectural boundary between **Lossless Ingestion (The Compiler)** and **Domain Cleaning / Relational Merging (The Composable Prepare Node)**, governed by a **3-Tier Decision Engine** and **Human-In-The-Loop (HITL) Merger Recommendations**.

---

## 1. Core Architectural Paradigm: The End of "Winner-Takes-All"

### 1.1 The Legacy Weakness
In standard ingestion architectures (including AIConnex v1.0), parser selection follows a priority-based, winner-takes-all scoring mechanism. When an archive is probed, the plugin with the highest confidence and priority score claims the dataset, and all other plugins are discarded.
* **The Failure Mode**: When processing heterogeneous archives (e.g., `plant.zip` containing `telemetry.xlsx`, `maintenance.json`, `calibration.xml`, and `README.pdf`), a high-priority tabular parser (like `scada_excel_parser`) claims the Excel file and silently ignores the maintenance logs, calibration constants, and documentation.

### 1.2 The v2.0 Cooperative Pipeline & Fusion Engine
To achieve the design goal—*"There should be almost no chance that Scout cannot understand a new industrial dataset"*—AIConnex v2.0 replaces single-parser competition with a **Cooperative Multi-Parser Execution Map**:

```
[ Heterogeneous Industrial Archive ] (e.g. plant.zip)
  ├── 1. SCADA_data.tdms       (LabVIEW Vibration Telemetry)
  ├── 2. maintenance.sqlite    (Relational Maintenance Logs)
  ├── 3. calibration.xml       (PLC Sensor Constants)
  └── 4. README.pdf            (Experiment Notes & Units)
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│ STAGE 1: ARCHIVE MANIFEST DISCOVERY (Plugin 90)         │
│ ➔ Scans entire archive, categorizes every file by type. │
│ ➔ Emits comprehensive archive tree & format inventory.  │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│ COOPERATIVE PARSER PIPELINE (Concurrent Multi-Routing)  │
│ ├── Route .tdms   ──> tdms_parser         ──> Table A   │
│ ├── Route .sqlite ──> sqlite_parser       ──> Table B   │
│ ├── Route .xml    ──> xml_parser          ──> Table C   │
│ └── Route .pdf    ──> text_meta_harvester ──> JSON Meta │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│ THE FUSION ENGINE (Assembler + Normalizer Stage)        │
│ ➔ Aligns Table A, B, and C on timestamp and asset_id.   │
│ ➔ Injects calibration XML & PDF units into schema_map.  │
│ ➔ Emits unified multi-modal dataset & metadata catalog. │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Split of Responsibility: Compiler vs. Data Prepare Node

### 2.1 The Anti-Pattern of "Blind Merging"
A foundational rule in AIConnex v2.0 is: **The Compiler must NEVER blindly merge datasets or execute lossy data cleaning.** 
Merging uncleaned, unaligned telemetry across physical assets creates severe data corruption:
* **Multi-Plant SCADA**: Merging Plant A (1-second sampling, `-9999` nulls) and Plant B (10-minute sampling, `NaN` nulls) before cleaning causes ML models to train on `-9999.0` as physical voltage readings and corrupts temporal anomaly detection.
* **NASA C-MAPSS Engines**: Concatenating engines across different flight altitudes (FD002/FD004) without regime normalization causes models to misinterpret high-altitude climbs as catastrophic engine failures.

### 2.2 Compiler Responsibilities (Stage 1–5 Ingestion Layer)
The Compiler is an **immutable, lossless extraction and syntactic normalization engine**:
1. **Recursive Unpacking**: Unpacks nested archives up to arbitrary depth (integrating Microsoft `RecursiveExtractor` capabilities for `.7z`, `.rar`, `.cab`, `.iso`).
2. **Lossless Format Parsing**: Converts binary structs (`.mat`, `.hdf5`, `.tdms`) into canonical Parquet/CSV table streams without discarding non-tabular phases (e.g., preserving charging phases and EIS impedance sweeps).
3. **Syntactic Normalization**: Casts timestamps to standard ISO-8601 strings, converts headers to lowercase `snake_case`, and infers data types.
4. **Partition Isolation**: Emits **isolated, individual partition tables** (1 table per physical asset/turbine/engine) along with a rich **Schema & Metadata Catalog** (`batch_manifest.json`, `schema_map.json`, `archive_intelligence_report.json`).

### 2.3 Data Prepare Node Responsibilities (Composable MLOps Node)
The Data Prepare Node is not a static stage; it is a **composable, stateless functional operator (`CleanNode`)** callable via REST API anywhere in the pipeline DAG:
1. **Domain Sentinel Scrubbing**: Scans numeric columns for domain error codes (`-9999.0`, `-1.0`, `"ERR"`, `"N/A"`) and imputes standard nulls (`NaN` / `None`).
2. **SCADA PLC Quality Filtering**: Drops or masks sensor rows where OPC-UA quality status flags indicate sensor freeze, disconnect, or maintenance (`status != 192`).
3. **Temporal Resampling & Alignment**: Aligns asynchronous time series (e.g., resampling 1-second turbine streams and 15-minute weather streams onto a uniform 10-minute time grid using statistical aggregations).
4. **Operating Regime Normalization**: In multi-regime datasets, clusters operating conditions into discrete regimes $R_1 \dots R_k$ and applies Z-score residual normalization ($Z = \frac{X - \mu_R}{\sigma_R}$) within each regime.
5. **Controlled Relational Merging**: Executes HITL-approved mergers (e.g., running SQL **ASOF JOINs** between telemetry and weather tables, or **UNIONing** cleaned plant partitions).

```
[ Raw Ingestion / Archive ]
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ COMPILER (Unpack & Parse Losslessly)                   │
└────────────────────────────────────────────────────────┘
           │
           ▼
   ( CALL CleanNode: Stage 1 - Syntactic & Sentinels )   <-- Called right after extraction
           │
           ▼
[ Cleaned Individual Partitions ] (e.g. Turbine A, Turbine B)
           │
           ▼
   ( CALL CleanNode: Stage 2 - PLC Quality Flags )       <-- Called BEFORE merging!
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ SQL MERGER / JOIN NODE (ASOF JOIN / UNION)             │
└────────────────────────────────────────────────────────┘
           │
           ▼
   ( CALL CleanNode: Stage 3 - Post-Join Imputation )    <-- Called AFTER merging!
           │
           ▼
[ Final ML Training Matrix ]
```

---

## 3. The 3-Tier Decision Engine & HITL Merger Governance

### 3.1 Who Decides When Cleaning Is Needed Before Merger?
The decision to invoke `POST /api/v1/prepare/clean` before merging is governed by an automated **3-Tier Decision Engine**:

| Tier | Layer | Mechanism & Trigger | Action Emitted |
|---|---|---|---|
| **Tier 1** | **Deterministic Profiler** (Stage 4) | Checks hard mathematical thresholds: Sentinel rate $> 0\%$, OPC-UA quality flag errors, or sampling frequency mismatch across partitions. | Emits `requires_pre_clean: true` and attaches required cleaning recipes. |
| **Tier 2** | **LLM Semantic Intelligence** (Stage 7) | Analyzes domain semantics, multi-regime confounders (e.g., flight Mach numbers), and physical table grain. | Emits semantic reasoning: *"Regime Z-score normalization is mandatory before merging."* |
| **Tier 3** | **DAG Orchestrator** (Dynamic Router) | Evaluates manifest flags from Tier 1 and Tier 2. | Conditionally injects `POST /prepare/clean` into execution graph before merger node. |

### 3.2 Human-In-The-Loop (HITL) Merger Governance
Even when the 3-Tier Engine resolves the exact cleaning and merger strategy, **the system must never blindly execute a relational merger without Human-In-The-Loop (HITL) confirmation** (unless explicitly operating in automated headless/batch mode).
* In Stage 7 (`problem_discovery`), the LLM generates structured **HITL Intent Options** (e.g., Option 1: Single Unified Vertical Stack vs. Option 2: Per-Partition Batching with separate models).
* The Compiler API returns the **Dataset Card** to the UI/TUI, presenting the LLM's **Recommendation** alongside a transparency report on detected noise and required pre-cleaning.
* The human engineer holds ultimate governance, reviewing the trade-offs and clicking **[Approve Recommended Strategy]** before the orchestrator fires the execution DAG.

---

## 4. Engineering Fixes for Operational Gaps (NASA Battery & SCADA Case Studies)

To permanently resolve the three operational nuances identified during the NASA Battery Data Set audit, the following engineering specifications are integrated into AIConnex v2.0:

### 4.1 Fix 1: Loss of Non-Tabular Environmental Context (`README.txt`)
* **Problem**: In a winner-takes-all model, `mat_parser` claimed the dataset, leaving 10 `README*.txt` files ignored and losing critical ambient operating temperatures ($24^\circ\text{C}$, $4^\circ\text{C}$, $43^\circ\text{C}$) and cutoff voltage thresholds.
* **Architectural Fix (`text_metadata_harvester.py`)**:
  1. All documentation files (`.txt`, `.pdf`, `.docx`, `.md`) are routed concurrently to the `text_metadata_harvester` plugin.
  2. The harvester invokes the local LLM (`gpt-oss:120b-cloud`) to extract physical experimental conditions into a structured dictionary:
     ```json
     {
       "B0005": {"ambient_temp_c": 24.0, "cutoff_voltage_v": 2.7},
       "B0045": {"ambient_temp_c": 4.0,  "cutoff_voltage_v": 2.0},
       "B0049": {"ambient_temp_c": 43.0, "cutoff_voltage_v": 2.0}
     }
     ```
  3. **Fusion Engine Injection**: The Assembler (or Prepare Node) joins this dictionary against `asset_id`, automatically injecting `ambient_temp_c` and `cutoff_voltage_v` as physical covariate columns into every partition table.

### 4.2 Fix 2: Unrecorded Non-Discharge Cycles (EIS & Charge)
* **Problem**: Single-stream filtering (`if type == 'discharge'`) silently discarded 170 charge cycles and 278 Electrochemical Impedance Spectroscopy (EIS) frequency sweeps per battery without cataloging them in `join_audit.json`.
* **Architectural Fix (Multi-Stream Lossless Extraction)**:
  1. `mat_parser.py` is upgraded to unpack all cycle types into independent data streams:
     * Primary Stream: `<asset>_discharge_cycles.parquet` (Time-domain degradation).
     * Secondary Stream: `<asset>_charge_cycles.parquet` (Time-domain charging profiles).
     * Tertiary Stream: `<asset>_impedance_eis.parquet` (Frequency-domain Nyquist sweeps: $Z_{\text{real}}, Z_{\text{imag}}$ vs. Frequency Hz).
  2. **Audit Cataloging**: The compiler records all extracted streams in `join_audit.json`:
     ```json
     {
       "asset_id": "B0007",
       "primary_active_stream": {"type": "discharge", "rows": 168, "file": "partitions/b0007_discharge.parquet"},
       "secondary_preserved_streams": {
         "charge": {"cycles": 170, "status": "preserved_in_raw_store"},
         "impedance_eis": {"cycles": 278, "status": "preserved_in_raw_store"}
       }
     }
     ```
  3. **MLOps Exploitation**: Downstream nodes can now query `secondary_preserved_streams`, run equivalent circuit feature extraction on EIS sweeps to compute internal battery resistance ($R_0$), and join $R_0$ onto the discharge feature matrix.

### 4.3 Fix 3: Standardized Dual-Footprint Telemetry Contract
* **Problem**: Discrepancies between compressed archive footprint reporting (SchemaGate) and uncompressed extracted workspace reporting (Stage 1 Discovery).
* **Architectural Fix**: All compiler manifests (`compiler_report.json`, `archive_intelligence_report.json`, `batch_manifest.json`) must embed a standardized **Storage Footprint Block**:
  ```json
  "storage_footprint": {
    "compressed_archive": {"bytes": 209708670, "megabytes": 199.99, "format": "zip_container"},
    "uncompressed_inventory": {"bytes": 419330801, "megabytes": 399.89, "decompression_ratio": 2.00},
    "inventory_breakdown": {
      "total_files_discovered": 54,
      "tabular_tables_parsed": 34,
      "documentation_files_harvested": 10,
      "nested_archives_unpacked": 6
    }
  }
  ```

---

## 5. End-to-End Microservice Data Handoff Contract

To guarantee seamless interoperability across AIConnex REST API microservices, the exact input/output payloads for the core execution nodes are standardized as follows:

### 5.1 Compiler + Scout Agent Output Payload (The Handoff Bundle)
Emitted to workspace object storage upon compilation completion:
* `batch_manifest.json`: Execution blueprint listing partition IDs, file URIs, and target column (`RUL`).
* `schema_map.json`: Canonical taxonomy mapping raw columns to MLOps roles (`Entity Key`, `Time Index`, `Target`, `Features`).
* `archive_intelligence_report.json`: Semantic card containing LLM physical definitions, domain classification, and HITL merger decision.
* `compiler_lock.json`: Deterministic lineage lock of plugin versions and execution hashes.
* `/partitions/*.parquet`: Losslessly extracted, syntactically normalized partition data tables.
* Pre-Merge Cleaning Flags: Boolean triggers and recipes for required downstream scrubbing.

### 5.2 Data Prepare Node API Contract (`POST /api/v1/prepare/execute`)
* **Input Payload**: `batch_manifest.json` URIs, `schema_map.json`, Pre-Merge Cleaning Flags, and selected cleaning recipe.
* **Execution Steps**: 
  1. Scrub sentinels (`-9999` $\rightarrow$ `NaN`).
  2. Filter SCADA PLC quality tags (`status == 192`).
  3. Resample asynchronous time grids (e.g., 1s $\rightarrow$ 10min).
  4. Execute Z-score regime normalization.
  5. Execute HITL-approved SQL merge (ASOF JOIN or UNION).
* **Output Payload**: `prepared_dataset.parquet` (Clean, aligned, imputed, regime-normalized ML feature matrix).

### 5.3 EDA Node API Contract (`POST /api/v1/eda/generate`)
* **Input Payload**: Raw compiled tables (from Compiler), clean feature matrix (from Prepare Node), and LLM semantic labels (from `archive_intelligence_report.json`).
* **Execution Steps**:
  1. Plot physical feature distributions and histograms using human-readable LLM titles.
  2. Compute Pearson/Spearman correlation matrices and target heatmaps.
  3. Plot time-series degradation trajectories across asset lifecycles.
  4. Generate side-by-side visual audits comparing raw sensor noise (before cleaning) against imputed signals (after cleaning).
* **Output Payload**: Interactive HTML dashboard (`eda_report.html`), summary statistical JSON, and rendered PNG charts for UI display.

---

## 6. Verified Code Gaps (7–15) & Architecture v2.0 Remediation Matrix

An exhaustive, line-by-line code audit of AIConnex v1.0 identified 9 additional architectural gaps across the plugin ecosystem, orchestrator, and registry. Below is the authoritative mapping of how AIConnex Architecture v2.0 systematically remediates every verified gap, alongside the macro-architectural solutions bridging the Intelligence Layer and MLOps execution nodes.

### 6.1 Line-by-Line Remediation Matrix

| # | Verified Gap in v1.0 | Root Cause in Live Code | Architecture v2.0 Remediation & Enforcement |
|---|---|---|---|
| **Gap 7** | **Cartesian Guard checks original row count, not cumulative count.** | `relational_join_assembler.py`: `fact_rows_before` is set once before the loop. In a 3+ table chain (A → B → C), cumulative row explosions bypass the guard. | **DAG-Based Cumulative Guard**: In v2.0's Fusion Engine, Cartesian explosion guards evaluate $\text{rows}(\text{state}) \le \tau \times \sum \text{rows}(\text{inputs})$ at every edge of the join DAG, terminating explosions dynamically. |
| **Gap 8** | **RUL cap of 125 is hardcoded for all datasets.** | `relational_join_assembler.py`: `clip(upper=125)`. Hardcoded for C-MAPSS turbofans; clips battery and IGBT aging datasets incorrectly. | **Dynamic Domain Target Constraints**: Stage 7 (`problem_discovery`) infers domain constraints and emits `target_constraints.clip_upper` in `archive_intelligence_report.json`. Hardcoded numerical clipping is banned. |
| **Gap 9** | **Excel header scan breaks on numeric text in headers.** | `scada_excel_parser.py`: `any(c.isdigit())` terminates scan prematurely on tokens like `"100kPa"` or `"2026"`, treating headers as data rows. | **Cooperative Type-Consistency Scanning**: Replaces regex heuristics with structural column type uniformity over $N$ subsequent rows, ensuring immunity to numeric header tokens. |
| **Gap 10** | **`degraded=True` fires even on clean deterministic runs.** | `orchestrator.py`: `if self.orchestrator.llm is None: report.degraded = True` fires on deterministic Stage 1/4 exits when LLM is disabled. | **Decoupled Observability Telemetry**: Introduces explicit runtime statuses (`execution_mode = "deterministic_headless"` vs. `"llm_assisted"`). `degraded` is only asserted upon error recovery fallbacks. |
| **Gap 11** | **Domain hint always None (Stage 6 before Stage 7).** | `orchestrator.py`: Stage 6 tries to read `problem_hypothesis.domain`, which is not populated until Stage 7 runs. | **Two-Pass Joint Intelligence Fusion**: Merges Stage 6 and 7 into an iterative loop. Pass 1 infers domain and target; Pass 2 resolves sensor tags using the confirmed domain context. |
| **Gap 12** | **`vertical_stack_assembler` ignores `CompilationStrategy`.** | `vertical_stack_assembler.py`: `assemble()` concatenates everything without reading `context.strategy.merge_rule`. | **Strict Strategy Routing Enforcement**: Base assembler class asserts compatibility with `CompilationStrategy`. If `merge_rule == "keep_separate"`, vertical stacking is rejected at routing time. |
| **Gap 13** | **Normalizer produces duplicate column names silently.** | `canonical_schema_normalizer.py`: Semantically similar strings (e.g. `"Pressure (bar)"` and `"Pressure_bar"`) normalize to identical names, creating duplicate DataFrame indices. | **Deterministic Collision Resolution**: Enforces deduplication (`pressure_bar_1`, `pressure_bar_2`) upon naming collision and emits an explicit warning in `schema_map.json` for Prepare Node resolution. |
| **Gap 14** | **Harvester ignores `tables` parameter, re-reads raw files.** | `signal_summary_harvester.py`: Bypasses `tables` parameter and re-reads disk paths from `context.inventory`, breaking microservice contracts. | **In-Memory Handoff Contract Enforcement**: Bypassing in-memory `DataFrame` payloads to re-read temporary disk files is prohibited. All harvesters must operate strictly on injected `tables`. |
| **Gap 15** | **`PluginRegistry` frozen after first compile, never unfrozen.** | `registry.py` + `compiler.py`: Permanent process-level `_is_frozen = True` causes live servers to ignore newly promoted Scout Agent plugins. | **Dynamic Registry Lifecycle Management**: `ScoutAgent.promote_plugin()` explicitly triggers `registry.reload_and_unfreeze()`, enabling live server hot-reloading without process restarts. |

---

### 6.2 Macro-Architectural Synthesis: Bridging Intelligence to Execution

Beyond fixing individual plugin bugs, Architecture v2.0 resolves the three macro-structural disconnects identified during the code audit:

#### 1. Activating the Intelligence Layer in Node 1 (ML Profiler & Feature Engineering)
* **The v1.0 Disconnect**: `archive_intelligence_report.json` contained rich LLM semantic reasoning (*"v_mean = Mean cell voltage"*), but Node 1 (ML pipeline) received an old heuristic `dataset_card` with hardcoded labels (*"Aerospace / Turbofan"*).
* **The v2.0 Solution**: The microservice handoff contract mandates that Node 1 (Prepare & EDA Node) directly consumes `archive_intelligence_report.json` and `schema_map.json`. Automated feature engineering scripts and EDA plotting libraries dynamically bind to the LLM's decoded physical names and units, ensuring domain reasoning directly shapes model training.

#### 2. Hard-Wiring HITL Strategy into Execution Routing
* **The v1.0 Disconnect**: A user could select `per_partition_batch` in the HITL UI, but if `vertical_stack_assembler` won the priority competition, it silently concatenated all partitions into a single CSV.
* **The v2.0 Solution**: The HITL selection is locked into `compiler_lock.json` and `batch_manifest.json`. The Fusion Engine's DAG Router treats the HITL decision as an immutable routing constraint, bypassing incompatible assemblers entirely and guaranteeing execution fidelity.

#### 3. Closed-Loop Scout Agent Self-Healing in Live Production
* **The v1.0 Disconnect**: Long-running API servers suffered from frozen plugin registries (Gap 15), rendering Scout Agent code promotions ineffective until manual server restarts occurred.
* **The v2.0 Solution**: By pairing dynamic registry unfreezing with the Cooperative Parser Pipeline, the Scout Agent achieves true zero-downtime autonomous self-healing in production Kubernetes environments.

---

## 7. The Recommended 11-Plugin Expansion & SCADA Ingestion Taxonomy

To operationalize the Cooperative Parser Pipeline and support 99% of industrial SCADA, IoT, and test-bench workloads, AIConnex Architecture v2.0 mandates the implementation of an **11-Plugin Expansion Set** organized across the four core lifecycle stages.

### 7.1 The Four-Stage Separation of Concerns Rule
A fundamental engineering command of Architecture v2.0 is:
> **"Do not make the parser responsible for deciding business merges. Do not make the compiler silently clean or harmonize semantics. Let the pipeline do this: Discovery decides what it is. Parser reads it. Assembler combines compatible pieces. Normalizer makes the output ML-safe."**

### 7.2 The 11-Plugin Expansion Set

#### Stage 1: Discovery Plugins (Deciding what it is)
1. **`archive_manifest_discovery`**: Opens compressed archives (`.zip`, `.tar`, `.7z`) and recursively catalogs every inner file member, folder layout, and file extension before any parser is invoked.
2. **`schema_fingerprint_discovery`**: Computes structural signatures across discovered tables to automatically classify whether files in a directory are same-schema monthly logs, mixed-schema relational bundles, or independent asset streams.
3. **`mixed_archive_router` (The Core Traffic Controller)**: The architectural replacement for winner-takes-all routing. It inspects the bundle manifest, splits files by format and role, and dispatches each file concurrently to its respective specialized parser while preserving raw file lineage.

#### Stage 2: Parser Plugins (Reading without lossy filtering)
4. **`tdms_parser`**: Native LabVIEW `.tdms` ingestion using `nptdms`. Essential for high-frequency vibration, acoustic, and motoring telemetry in test benches.
5. **`json_parser`**: Parses `.json`, `.jsonl`, and `.ndjson` streams. Vital for IoT gateway event logs, API exports, and SCADA alarms.
6. **`sqlite_parser`**: Extracts relational tables from `.db`, `.sqlite`, and `.sqlite3` files exported by edge historians and local asset databases.
7. **`xml_parser`**: Unpacks hierarchical XML schemas common in PLC exports, OPC-UA historians, and MES manufacturing systems.
8. **`text_delimited_autodetect_parser`**: A robust fallback parser for `.dat`, `.asc`, `.log`, and whitespace-delimited sensor dumps that automatically infers delimiters, headers, and numeric encoding.

#### Stage 3: Assembler Plugins (Combining compatible pieces)
9. **`multi_source_union_assembler`**: Stacks same-schema tables from multiple plants or monthly logs into unified partition tables after verifying schema fingerprint compatibility.
10. **`keyed_time_join_assembler`**: Executes interval joins and ASOF JOINs to combine asymmetric relational tables (e.g., joining high-frequency inverter telemetry with medium-frequency weather station dimensions on timestamp and asset key).

#### Stage 4: Normalizer Plugins (Making output ML-safe)
11. **`unit_standardizer`**: Converts physical engineering units into standardized SI/metric base units (e.g., converting `psi` $\rightarrow$ `bar`, `°F` $\rightarrow$ `°C`, `kW` $\rightarrow$ `W`) using LLM semantic definitions and engineering conversion dictionaries.

---

### 7.3 SCADA Ingestion Taxonomy: Optimization Hierarchy
For SCADA and industrial IoT environments specifically, data ingestion must be strictly optimized according to the following execution hierarchy:
1. **Format Detection First** (via `archive_manifest_discovery` + `mixed_archive_router`).
2. **Schema Detection Second** (via `schema_fingerprint_discovery` + LLM Stage 5/6).
3. **Source-Specific Cleaning Third** (via Composable `CleanNode` invoked on individual partitions).
4. **Relational Merging Last** (via HITL-governed `keyed_time_join_assembler` or SQL merger).
