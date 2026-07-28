# Industrial ML Pipeline: Architectural Decision Gates & Recommended Defaults

This document defines the 6 key decision gates for the AIConnex Machine Learning platform. For each gate, we outline the options, trade-offs, and recommended defaults. We validate these choices using recent industry benchmarks and the production architecture of **Sorba.ai**—an established industrial AI vendor.

---

## 1. What Sorba.ai Actually Does in Production

To build a competitive platform, we map our architecture against Sorba.ai's established patterns:

*   **Orchestration:** Sorba runs a patented distributed architecture ("Smart Operational Realtime Bigdata Analytics") spanning edge and cloud. It uses a proprietary Auto-ETL/Auto-ML orchestration layer rather than an open-source tool. Our design will use open, modular tools to differentiate on cost and prevent vendor lock-in.
*   **Edge Deployment:** Sorba runs AI processing directly on the plant floor for low-latency, real-time closed-loop control, partnering with ZEDEDA for edge orchestration and Velasea for ruggedized industrial hardware. This validates our design decision to avoid one-size-fits-all hardware assumptions and prioritize containerized edge portability.
*   **Schema Mapping & Onboarding:** Their "Smart Data Edge" component handles OT/IT ingestion from PLCs, SCADA, historians, MES, and ERP systems using low-level industrial drivers combined with high-level IoT connectors. This corresponds to our choice of a driver-based mapping layer.
*   **Model Deployment Format:** Sorba claims fault detection precision improvements of ~29% and robustness improvements of ~11% versus Apache Spark MLlib baselines. They support edge deployment for real-time predictions, but rely on compiled execution rather than raw Python runtime scripts at the edge.
*   **Drift/Retraining:** Sorba supports "auto-retraining" as an interface capability, pointing toward a semi-automated, configuration-driven retraining scheduler.

---

## 2. Pros/Cons Research & Benchmark Validation

*   **Orchestrator Comparisons (Prefect vs. Airflow vs. Dagster vs. Metaflow):** 
    *   *Prefect* excels at Python-native simplicity and a hybrid SaaS model that keeps the actual raw data within your local infrastructure.
    *   *Airflow* offers mature scheduling but is operationally heavy and hard to debug.
    *   *Dagster* provides top-tier data lineage (asset-tracking) but introduces a significant configuration learning curve.
*   **Edge Inference Formats (ONNX vs. Treelite):** 
    Benchmarks on a Raspberry Pi 4 for LightGBM anomaly detection reveal a critical trade-off:
    *   **ONNX INT8 Quantization:** Achieves a **40x speedup** for real-time single-inference but runs with a high CPU and thermal load.
    *   **Treelite C-Compilation:** Achieves a **13x speedup** but with extremely low CPU utilization (~26%).
    *   *Takeaway:* **Treelite is superior for sustained/batch inference** on low-power edge systems, while **ONNX is better for single-shot, latency-critical predictions** or deep learning models.
*   **ONNX vs. TFLite:** ONNX runtime provides broader framework flexibility (Scikit-Learn, XGBoost, PyTorch) compared to TensorFlow Lite (which is strictly optimized for TensorFlow). This fits our multi-framework algorithm registry.

---

## 3. The 6 Decision Gates

```
               ┌───────────────────────────────────────────────┐
               │          THE 6 DECISION GATES MENU            │
               └──────┬─────────────────────────────────┬──────┘
                      │                                 │
         ┌────────────▼────────────┐       ┌────────────▼────────────┐
         │ GATE 1: ORCHESTRATION   │       │ GATE 2: DATA RESAMPLING │
         │ • Custom Python Runner  │       │ • In-Memory Pandas/Polars│
         │ • Prefect (Hybrid SaaS) │       │ • Database Push-down    │
         └─────────────────────────┘       └─────────────────────────┘
                      │                                 │
         ┌────────────▼────────────┐       ┌────────────▼────────────┐
         │ GATE 3: THRESHOLD CALIB │       │ GATE 4: EDGE RUNTIME    │
         │ • Statistical Percentile│       │ • Treelite (Batch/Tree) │
         │ • Cost-Optimization     │       │ • ONNX (Latency/DL)     │
         └─────────────────────────┘       └─────────────────────────┘
                      │                                 │
         ┌────────────▼────────────┐       ┌────────────▼────────────┐
         │ GATE 5: SCHEMA MAPPING  │       │ GATE 6: DRIFT RESPONSE  │
         │ • File-Based Config Map │       │ • Multi-Tier Hybrid     │
         │ • DB Tag Registry       │       │ • Human-Gated Retrain   │
         └─────────────────────────┘       └─────────────────────────┘
```

### Gate 1: Workflow Orchestrator (How do we coordinate the steps?)
*   **Option A:** Custom Python Runner (`runner.py`)
*   **Option B:** Prefect (Python-first, dynamic orchestration)
*   **Option C:** Metaflow (Data-scientist-centric, built-in versioning/infra abstraction)
*   **Option D:** Dagster (Asset-oriented data orchestration)

### Gate 2: Data Resampling & Time-Alignment Strategy (How do we handle multi-rate sensors?)
*   **Option A:** Database/ETL-level alignment (e.g. TimescaleDB, InfluxDB doing the downsampling before Python gets it)
*   **Option B:** Pandas/Polars in-memory resampling (flexible, but memory-intensive for large datasets)
*   **Option C:** Event-driven step-alignment (each event triggers feature calculation on-the-fly)

### Gate 3: Anomaly Threshold Calibration (How sensitive are alarms?)
*   **Option A:** Statistical Percentile (e.g., 99th percentile of healthy validation data)
*   **Option B:** Extreme Value Theory (EVT) (mathematically models the extreme tail for low false-alarm rates)
*   **Option C:** Cost-Sensitive Optimization (SME-defined cost weights for false alarm vs. missed detection)

### Gate 4: Edge Deployment Format (How is the model executed at the edge?)
*   **Option A:** Raw Python + Pickled Model (standard, easiest, but requires Python environment on edge)
*   **Option B:** Compiled C/C++ shared library (via Treelite for tree ensembles)
*   **Option C:** ONNX Runtime (highly standardized, cross-language, great for neural nets and some tree models)

### Gate 5: Multi-Tenant Schema Mapping Configuration (How do we map site tags?)
*   **Option A:** Static JSON configuration files per tenant
*   **Option B:** Dynamic database tag registry (queried via API at runtime)
*   **Option C:** Code-based tenant classes (inheritance per plant)

### Gate 6: Drift Response Policy (What do we do when data shifts?)
*   **Option A:** Fully Automated Retraining Loops
*   **Option B:** Human-in-the-Loop Gatekeeper
*   **Option C:** Multi-Tier Auto-Routing (Hybrid)

---

## 4. Suggested Defaults (Recommended Architecture Path)

Based on the research findings and benchmarks, we suggest the following defaults for the AIConnex implementation:

| Gate | Recommended Default | Rationale |
| :--- | :--- | :--- |
| **Gate 1: Orchestration** | **Option A (Custom Runner) $\rightarrow$ Prefect Roadmap** | Start with a zero-dependency custom Python runner to speed up MVP prototyping. Migrate to Prefect once the platform needs central pipeline visualization and automated task retries. |
| **Gate 2: Resampling** | **Option B (In-Memory Polars) $\rightarrow$ Option A Push-down** | Use in-memory Polars dataframes for the initial notebook/SageMaker development phases. Evolve to Database-level (push-down) resampling once deploying to high-frequency multi-site production databases. |
| **Gate 3: Thresholding** | **Option A (Statistical Percentile) $\rightarrow$ Option C Cost-Opt** | Start with a simple 99% statistical percentile threshold. It is explainable to plant operators. Evolve to Option C (cost-optimization matrices) once real-world financial cost metrics for downtime vs. false alarms are obtained from clients. |
| **Gate 4: Edge Runtime** | **Hybrid Treelite & ONNX** | Do not pick a single format. Use **Treelite for decision tree models** (XGBoost/LightGBM) to minimize CPU load on edge hardware. Use **ONNX for deep learning models** or mixed architectures where single-shot low latency is required. |
| **Gate 5: Schema Mapping** | **Option A (Config Files) $\rightarrow$ Option B DB Registry** | Use file-based JSON config maps for initial pilot sites. Transition to a database-driven tag registry once building a multi-tenant portal where users configure tag mappings dynamically through a UI. |
| **Gate 6: Drift Response** | **Option C (Multi-Tier Hybrid)** | If anomaly scores drift, auto-recalibrate the threshold first (cheap/fast). If input features drift entirely out of bounds, trigger a candidate retraining run but gate the final production deployment behind human approval. |

---

## 5. Strategic Takeaway

Sorba's primary competitive advantage is not a proprietary modeling algorithm. It is their **speed of site onboarding** and their **edge stability**. 

By selecting **Option A $\rightarrow$ B** for Schema Mapping (Gate 5) and utilizing a **Hybrid ONNX/Treelite Runtime** (Gate 4), we achieve comparable edge reliability and fast setup times using a modular, open-source stack that we own 100%.
