<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Also a list of what Apache Framework n Tools that we are Gonna use

Below is the **Apache-only list** for the current AI-ConneX architecture, separated into **adopt now**, **use when needed**, and **do not introduce yet**.

# Apache Tools to Use Now

| Apache tool | AI-ConneX location | Exact use |
| :-- | :-- | :-- |
| **Apache Arrow** | Parser, Compiler, Profiler and PREPARE | Common in-memory columnar representation |
| **Apache Parquet** | Dataset artifact storage | Canonical typed, compressed and partitioned format |
| **Apache DataFusion** | Dataset inspection, Compiler, Profiler and SQL execution | Query CSV/Parquet and execute validated transformations |
| **Apache Airflow** | Scheduled workflow layer | Batch ingestion, reprocessing, profiling, retraining and drift checks |

## Apache Arrow

Use Arrow as the internal data interchange layer:

```text
Parser
  → Arrow RecordBatch/Table
  → DataFusion
  → Arrow result
  → Parquet
```

Arrow lets the ingestion, profiling and transformation services share a standard columnar representation rather than repeatedly converting between incompatible formats.

## Apache Parquet

Use Parquet for:

- Parsed datasets.
- Compiled datasets.
- Prepared datasets.
- Feature datasets.
- Analytical results.
- Intermediate data exchanged between services.

Recommended storage layout:

```text
tenant/site/dataset/
├── raw/
├── parsed/
├── compiled/
├── prepared/
├── features/
├── reports/
└── lineage/
```


## Apache DataFusion

Use DataFusion for:

- CSV and Parquet inspection.
- Schema discovery.
- SQL projections.
- Joins.
- Aggregations.
- Partition pruning.
- Profiling scans.
- Conditional compilation.
- Data-quality calculations.

DataFusion provides SQL and DataFrame interfaces and supports CSV and Parquet through Python bindings.[^1][^2]

## Apache Airflow

Use Airflow for workflows that are:

- Scheduled.
- Batch-oriented.
- Retryable.
- Dependency-heavy.
- Operationally observable.

Examples:

```text
Nightly data reprocessing
Weekly client-data profiling
Historical backfills
Batch anomaly detection
Scheduled model retraining
Drift evaluation
Parquet compaction
Audit and usage rollups
```

Airflow should not own:

- Per-message intent classification.
- Jane conversation state.
- Dynamic user clarification.
- Human approval state.
- The Agent Runtime loop.

***

# Apache Tools for Later

These tools are valuable, but should be introduced only when the workload requires them.


| Apache tool | Add when | Future role |
| :-- | :-- | :-- |
| **Apache Kafka** | Multiple sites or continuous telemetry streams | Durable event buffer, replay and decoupled ingestion |
| **Apache Beam** | Distributed or portable batch/stream processing | One pipeline model across local, Flink, Spark or cloud runners |
| **Apache Iceberg** | Parquet directories need table management | Snapshots, schema evolution, time travel and incremental reads |
| **Apache Spark** | Data exceeds single-server processing capacity | Distributed transformations and large-scale training preparation |
| **Apache Flink** | Low-latency event-time stream processing is required | Stateful streaming and real-time analytics |
| **Apache Kafka Connect** | Many external data-source connectors are required | Standardized source and sink integration |
| **Apache Hudi** | Frequent record updates and incremental ingestion are needed | Upserts, incremental processing and data-lake tables |
| **Apache Ozone** | Large private-cloud object storage is required | Distributed object storage |

Apache Beam is a unified programming model for batch and stream-processing pipelines, but it is not needed for the first local Docker-based ingestion path.[^3][^4]

***

# Apache Tools Not Needed Yet

Do not add these to the first implementation unless there is a specific operational requirement:


| Tool | Why defer |
| :-- | :-- |
| **Apache Spark** | Adds cluster-management overhead when DataFusion and Arrow handle the current workload |
| **Apache Flink** | Not needed until low-latency stateful streaming is required |
| **Apache Beam** | Adds runner and pipeline complexity for local file ingestion |
| **Apache Iceberg** | Parquet is sufficient before snapshot/concurrent-table needs appear |
| **Apache Kafka** | Overkill for occasional file uploads |
| **Apache Ozone** | MinIO/S3 is simpler for the current artifact layer |
| **Apache Hive** | Not required for the current service-oriented architecture |
| **Apache ZooKeeper** | Avoid unless a selected Apache system specifically requires it |


***

# Non-Apache Components Still Required

Apache tools do not cover every part of AI-ConneX.


| Area | Recommended non-Apache technology | Purpose |
| :-- | :-- | :-- |
| API | FastAPI + Uvicorn | Application and service APIs |
| Contracts | Pydantic + JSON Schema | Typed request and artifact validation |
| Agent planning | LangGraph | Dynamic routing, clarification and stateful planning |
| Routing model | Qwen3-4B or similar | Intent classification |
| Code/SQL proposal | Qwen2.5-Coder | Proposals executed only in Docker |
| Narration | Phi-4-mini or similar | Explain validated results |
| DataFrame processing | Polars | Fast DataFrame operations |
| Quality validation | Great Expectations | Expectations, validation suites and reports |
| Model training | scikit-learn | Classical ML pipelines |
| Time series | AutoTS, PyCaret, StatsForecast | Forecasting |
| Feature extraction | tsfresh, only with controls | Automated time-series features |
| Experiment tracking | MLflow | Experiments, metrics and model registry |
| Feature registry | Feast or internal registry | Feature definitions and serving |
| Model serving | ONNX Runtime | Portable inference |
| Sandbox | Docker | Isolated parser/worker execution |
| Metadata | PostgreSQL | Jobs, manifests, lineage, users and policies |
| Local object storage | MinIO | Raw and processed artifacts |
| Observability | OpenTelemetry, Prometheus, Grafana | Traces, metrics and dashboards |
| Security | Vault/KMS, Trivy, Syft, Cosign | Secrets, scanning, SBOM and signing |


***

# Final Adopted Stack

## Current baseline

```text
FastAPI
Pydantic
LangGraph
PostgreSQL
Redis
MinIO
Docker

Apache Arrow
Apache DataFusion
Apache Parquet
Apache Airflow

Polars
Great Expectations
scikit-learn
MLflow
ONNX Runtime

OpenTelemetry
Prometheus
Grafana
```


## Apache portion specifically

```text
Apache Arrow
Apache Parquet
Apache DataFusion
Apache Airflow
```


## Later Apache expansion

```text
Apache Kafka
Apache Beam
Apache Iceberg
Apache Spark
Apache Flink
Apache Kafka Connect
```


# Final Tool Ownership

```text
Apache Arrow:
  In-memory data interchange

Apache DataFusion:
  Query and transformation engine

Apache Parquet:
  Canonical data storage

Apache Airflow:
  Scheduled and batch workflow orchestration

LangGraph:
  Dynamic per-request agent routing and clarification

Docker:
  Parser and transformation sandbox

Great Expectations:
  Data-quality validation

MLflow:
  Experiment and model lifecycle

PostgreSQL:
  Platform metadata and lineage

MinIO/S3:
  Raw and processed artifact storage
```

The key architectural decision is:

> **Use Apache Arrow, DataFusion and Parquet as the core data plane; use Airflow for scheduled operations; use Docker for isolated execution; and use LangGraph for dynamic agent-driven routing.**

This gives AI-ConneX an Apache-forward architecture without introducing Kafka, Beam, Spark, Flink or Iceberg before they are operationally justified.

<div align="center">⁂</div>

[^1]: https://datafusion.apache.org/python/autoapi/datafusion/io/index.html

[^2]: https://datafusion.apache.org/python/user-guide/io/csv.html

[^3]: https://beam.apache.org/documentation/

[^4]: https://beam.apache.org/

