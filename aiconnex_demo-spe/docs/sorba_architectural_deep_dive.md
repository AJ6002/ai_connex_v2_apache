# Deep-Dive Architectural Inspection Report: SORBA SDE (Edge)
**Target Platform:** SORBA.ai / SORBA SDE Container (`sorbotics/sorba-sde:latest`)  
**Inspection Date:** July 20, 2026  
**Auditor:** Antigravity (Google DeepMind Team)  

---

## 1. Executive Summary

A full architectural reverse-engineering of SORBA SDE was conducted by directly inspecting its multi-process Docker container (`my-sde`), NGINX reverse-proxy routing tables, MySQL database tables, Node.js API servers, and Python runtime virtual environments.

### Key Finding: Root Cause of Performance Bottlenecks & Lag
SORBA SDE runs as a **monolithic multi-process container** hosting over 40 concurrent microservices inside a single container instance. When a large dataset (>10 MB) is uploaded, SORBA triggers in-memory Python DataFrames (using `pandas`, `scikit-learn`, `shap`, and `scipy`) to compute statistical correlation matrices, data quality metrics, and tag rankings. Because all services (database, Node.js APIs, NGINX, and Python workers) compete for the same local Docker RAM allocation (typically 7.2 GB limit), processing large files causes immediate Out-Of-Memory (OOM) deadlocks, freezing the Docker daemon.

---

## 2. Container Internal Microservice Topology

Inside the `sorbotics/sorba-sde:latest` image, a Supervisord process daemon orchestrates 40+ microservices divided into distinct layers:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 NGINX Reverse Proxy                     │
                  │   (Port 80 HTTP -> 301, Port 443 SSL -> Apps Routing)    │
                  └───────────────────────────┬─────────────────────────────┘
                                              │
      ┌─────────────────────────┬─────────────┴───────────┬─────────────────────────┐
      ▼                         ▼                         ▼                         ▼
┌──────────────┐        ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│  Node.js UIs │        │ Node.js APIs │          │ Python VenVs │          │  Databases   │
├──────────────┤        ├──────────────┤          ├──────────────┤          ├──────────────┤
│ iot-unified  │        │ ml-trainer   │          │ sdc_ml_pred  │          │ MySQL (3306) │
│ ml-ui        │        │ tree-api     │          │ knowledge    │          │ InfluxDB     │
│ taskflow-ui  │        │ identity-api │          │ iot_connect  │          │ Redis (6379) │
│ sorbot-ui    │        │ taskflows-api│          │ task_exec    │          │ Mosquitto    │
│ Grafana      │        │ sde-socket   │          │ script_eng   │          │ (1883 MQTT)  │
└──────────────┘        └──────────────┘          └──────────────┘          └──────────────┘
```

### Microservice Inventory
1. **Frontend UIs (Node.js & Embedded Renders):**
   * `sorba-iot-unified-ui` (Port 3000 / Workspace UI)
   * `sorba-ml-ui` (Port 3019 / AI Trainer UI)
   * `sorba-task-flows-ui` (Port 3020 / Task Flow UI)
   * `Grafana` (`/usr/sbin/grafana-server` on Port 3000 for telemetry charts)
   * `Node-RED` (`node-red` for visual IoT workflow wiring)

2. **Backend API Servers (Node.js/Sequelize):**
   * `sorba-ml-trainer-api` (Port 5556 / ML Pipeline Orchestrator)
   * `sorba-tree-api` (Port 8089 / Asset Hierarchy & Device Collection Engine - 3 cluster workers)
   * `sorba-identity-api` (Port 3002 / Tenant & User Auth - 2 cluster workers)
   * `sorba-sde-socket` (Port 9006 / WebSocket real-time event engine with `--max-old-space-size=2048`)

3. **Python Execution Runtimes (`/usr/share/sde_venvs/`):**
   * `sdc_ml_predictor_runtime` (Python 3.11 environment hosting `sorba_ml`, `scikit-learn` 1.6.0, `xgboost` 3.2.0, `tensorflow` 2.16.1, `torch` 2.8.0, and `shap` 0.49.1)
   * `iot_connectors` (Python environment for PLC/OPC-UA/Modbus drivers)
   * `knowledge_store` & `task_executor` (Python automation workers)

---

## 3. Relational Database Schema (`ml_trainer` DB)

SORBA uses MySQL with Sequelize ORM. Inspection of `ml_trainer` revealed a clean, multi-tenant object hierarchy:

```
[Tenants]
   └── [Users]
        └── [Datasets] (fields, timestamp_field, dashboard_data, status)
             └── [datasetVersions] (version "1.0.0", dashboard_data_hist)
                  └── [Projects] (tenant, datasetId)
                       └── [Analyses] (project, algorithm, pre_processor, dim_reduction)
                            └── [Models] (analysis, datasetVersions, best_estimator_parameter, model.zip)
                                 └── [Predicts] (model, datasetId, simulation_mode, simulation_interval)
```

### Key Schema Fields Discovered:
* **Multi-Tenancy:** Every table contains a mandatory `tenant varchar(255)` column (default: `sorba_sde`).
* **Processing Caps:** The `settings` table explicitly enforces datapoint ceilings for overview UI components:
  * `dataset_overview_max_datapoints`: `10000`
  * `algorithm_max_datapoints`: `10000`
  * `prediction_overview_max_datapoints`: `10000`
* **Underlying Engines:** Tables contain `livy_session_id` (Apache Livy for Spark) and `ray_id` (Ray.io for distributed Python execution).

---

## 4. On-Disk File & Artifact Persistence Model

All persistent assets are saved in `/opt/sdc/ml-trainer/sorba_sde/`:

1. **Dataset Directory (`/opt/sdc/ml-trainer/sorba_sde/datasets/<dataset_id>/`):**
   * `dashboard-data.json`: Pre-calculated statistical metrics (correlation heatmap matrix, data quality scores, tag rankings).
   * `dashboard_data_hist/1.0.0.json`: Historical version snapshot.
   * `job.py`: Dynamically generated Python script that executed dataset profiling.

2. **Model Directory (`/opt/sdc/ml-trainer/sorba_sde/projects/<proj_id>/analyses/<analysis_id>/models/<model_id>/`):**
   * `job.py`: Dynamically generated Python script that trained the Scikit-Learn / XGBoost model.
   * `model.zip`: Compressed archive containing:
     * `estimator/estimator.pkl`: Serialized Scikit-Learn / XGBoost model.
     * `preprocessing_input/preproc_input.pkl`: Serialized input feature scaler (`StandardScaler`).
     * `preprocessing_target/preproc_target.pkl`: Serialized target scaler.
     * `best-estimator-parameters.json`: Optimal hyperparameter configuration chosen by Auto-ML.

3. **Inference Directory (`.../models/<model_id>/predicts/<predict_id>/`):**
   * `job.py`: Generated Python script executing live prediction and simulation logic.
   * `offline_predictor_parameters.json`: Live inference configuration and anomaly thresholds.

---

## 5. Strategic Blueprint for AI ConneX

Based on this inspection, AI ConneX can achieve **complete functional parity** while completely avoiding SORBA's memory and performance traps:

| Architectural Surface | SORBA SDE Limitation | AI ConneX Decoupled Cloud Architecture |
| :--- | :--- | :--- |
| **Data Ingestion** | Local in-memory load crashes Docker containers on >10 MB files. | **S3 Decoupled Storage + AWS Glue / Spark Jobs** for large files; client-side chunking for uploads. |
| **Data Sanity** | Fails with HTTP 500 error if CSV headers contain spaces or special characters. | **Auto-Sanitizing Ingestion Pipeline**: Auto-strips spaces and replaces invalid chars with `_` before processing. |
| **Auto-ML Execution** | Monolithic local Python process bundling PyTorch, TensorFlow, and Scikit-Learn in one container. | **SageMaker Processing & Training Jobs**: Dedicated container per pipeline stage (`SKLearnProcessor` on `ml.t3.medium` / `ml.m5.large`). |
| **Pipeline Visualization** | Static wizard pages and multi-tab dashboards. | **ReactFlow Dynamic Workflow Canvas** + **Conversational Master Agent** (AI recommendations for feature selection and tuning). |
