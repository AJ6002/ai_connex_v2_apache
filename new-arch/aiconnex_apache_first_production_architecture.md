# AI-ConneX Apache-First Production Architecture
## Production Ingestion, Brain Routing, Sandboxed Execution and CI/CD

**Status:** Production-oriented architecture baseline

**Scope:** Chatbot/Jane → intent routing → dataset intake → conditional parsing/compilation → Data Studio Brain → non-ML or ML route → deployment and monitoring.

**Operating assumption:** Real client data is used for validation. The architecture therefore prioritizes mature Apache ecosystem components, explicit operational boundaries, auditability, deterministic validation and low custom pipeline code.

**Important constraint:** Agents never receive arbitrary shell access, arbitrary Python execution, direct Docker control, Airflow administrator permissions, unrestricted SQL, database credentials or unrestricted network access.

---

## 1. Executive Decision

Use Apache tools for the data plane and scheduled workflow plane, but do not force Apache Airflow to manage dynamic conversational routing.

```text
LangGraph / Agent Runtime
  → intent narrowing
  → clarification
  → dynamic per-request route
  → typed execution plan

Apache Airflow
  → scheduled ingestion
  → batch reprocessing
  → historical backfills
  → profiling schedules
  → retraining
  → drift jobs

Docker
  → simple sandbox for untrusted parser jobs

Apache Arrow / DataFusion / Parquet
  → data representation, querying and canonical storage

PostgreSQL / MinIO or S3
  → metadata, manifests, lineage and artifacts

Great Expectations
  → production data-quality validation

Kubernetes
  → future scale-out only; not required for the initial Docker-based deployment
```

Airflow DAGs are appropriate for scheduled and dependency-heavy workflows. They are not the right authority for per-request conversational state, clarification or durable human approval. The architecture therefore uses Airflow and the Agent Runtime for different responsibilities.

---

## 2. Complete Production Flow

```text
USER / INDUSTRIAL SYSTEM
          │
          ├── Jane / NLP session
          │
          └── File, API, MQTT or OPC UA input
                         │
                         ▼
              API Gateway and Intake Service
                         │
                         ▼
              Identity + Tenant Context
                         │
                         ▼
              Immutable Raw Asset Registration
                         │
                         ▼
              Archive Security Inspection
                         │
                         ▼
              Dataset Discovery Artifact
                         │
                         ▼
              Intent-Narrowing Planner
                         │
                         ▼
              Deterministic Plan Validator
                         │
                ┌────────┼────────┐
                ▼        ▼        ▼
          Clarification Parse   Compile / Analyze
                │        │        │
                └────────┴────────┘
                         │
                         ▼
                  Docker Parser Job
                         │
                         ▼
              Arrow → DataFusion → Parquet
                         │
                         ▼
              Output Validation and Promotion
                         │
                         ▼
                 Data Studio Brain
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Profiler     DAG/Recipe   PREPARE/Math
                         │          │
                         └────┬─────┘
                              ▼
                    Conditional Route Gate
                         │
                ┌────────┴────────┐
                ▼                 ▼
       Data Service / Math      ML Studio
          Visualization       STEM / Models
                │                 │
                └────────┬────────┘
                         ▼
             Deployment and Monitoring
```

---

## 3. Tool Ownership Matrix

| Layer | Production tool | Exact responsibility | Agent access |
|---|---|---|---|
| API | FastAPI + Uvicorn | Intake, job and status APIs | Via typed API only |
| Contracts | Pydantic + JSON Schema | Intent, plan, manifest and result contracts | Propose typed objects only |
| Conversation | LangGraph | Stateful intent narrowing and clarification | Agent state machine |
| Metadata | PostgreSQL | Jobs, tenants, manifests, lineage and policies | Scoped service APIs |
| Raw/artifacts | MinIO or S3 | Immutable uploads, Parquet and reports | URI references only |
| Archive handling | Python `zipfile`/`tarfile` | Member inspection and streaming reads | Never directly |
| Columnar memory | Apache Arrow/PyArrow | In-memory schema and table representation | Through parser capability |
| Query/compilation | Apache DataFusion | SQL/DataFrame reads, joins, projections and aggregations | Approved query templates only |
| Storage format | Apache Parquet | Canonical compiled/prepared output | Not directly |
| Quality | Great Expectations | Versioned expectation suites and validation reports | Read results only |
| Profiling | DataFusion + Arrow + Polars/NumPy | Structural/statistical/temporal profiling | Request profile job |
| Scheduling | Apache Airflow | Scheduled and batch workflows | Trigger allow-listed DAGs |
| Sandboxing | Docker | Disposable parser/transform workers | Never direct Docker access |
| Event streaming | Apache Kafka, later | Durable telemetry/event buffer and replay | Through event APIs |
| Portable pipelines | Apache Beam, later | Distributed batch/stream ingestion | Submit approved pipeline |
| Table management | Apache Iceberg, later | Snapshots, schema evolution and time travel | Through table service |
| CI | GitHub Actions | Tests, scans, image builds and reports | None |
| CD | Argo CD, if Kubernetes is adopted | GitOps deployment | Human-gated promotion |
| Observability | OpenTelemetry + Prometheus + Grafana | Traces, metrics, logs and dashboards | Read-only observability APIs |
| Security | Trivy + Syft + Cosign + Vault/KMS | Scanning, SBOM, signing and secrets | No direct secret access |

Apache Arrow’s dataset facilities support multi-file and potentially larger-than-memory datasets, while DataFusion provides Python interfaces for CSV and Parquet queries. [web:163][web:164][web:165]

---

## 4. Why This Is Apache-First but Not Apache-Only

Apache tools reduce custom data-engineering code, but they do not replace platform responsibilities.

Apache tools provide:

- Mature data formats.
- Query execution.
- Workflow orchestration.
- Streaming and distributed-processing options.
- Standardized project governance.
- Broad ecosystem integrations.

AI-ConneX still must implement:

- Intent contracts.
- Conditional compilation policy.
- Agent Plan Validator.
- Tenant and asset authorization.
- Data semantic interpretation.
- Domain-specific units and physical constraints.
- Model-selection policy.
- Human approvals.
- Lineage rules.
- Numeric-narration verification.
- Client-specific quality expectations.

The target is not zero custom code. The target is to keep custom code focused on AI-ConneX domain logic instead of rebuilding generic ingestion, storage, scheduling and query infrastructure.

---

## 5. Intake and Intent Layer

### 5.1 Services

Use:

- FastAPI for APIs.
- Pydantic for typed validation.
- PostgreSQL for durable sessions, intents and jobs.
- Redis for short-lived state and locks.
- LangGraph for bounded intent narrowing.
- OpenTelemetry for request traces.

### 5.2 Intent envelope

Every request should produce an immutable Intent Envelope containing:

```text
intent_uid
tenant_uid
user_uid
site_scope
asset_scope
goal
domain
requested_outputs
requires_model
requires_visualization
requires_service
autonomy_requested
constraints
source_refs
policy_ref
```

Tenant and user identity must come from the authenticated application context. The language model must not generate tenant permissions.

### 5.3 Intent narrowing

The planner should run:

```text
DISCOVER → UNDERSTAND → NARROW → PROPOSE → VALIDATE → CLARIFY or FINALIZE
```

Possible outcomes:

```text
PARSE_ONLY
PROFILE_ONLY
COMPILE
MATH_ANALYSIS
PREPARE
COMPILE_THEN_PROFILE
ROUTE_TO_ML
ROUTE_TO_AGENTIC
NEEDS_CLARIFICATION
NEEDS_USER_CORRECTION
BLOCK
```

The output is a typed plan, not executable code.

---

## 6. Raw Asset and Archive Handling

### 6.1 Raw asset lifecycle

```text
RECEIVED
  → HASHED
  → QUARANTINED
  → INSPECTED
  → APPROVED_FOR_PARSING
  → PARSED
  → VALIDATED
  → PROMOTED
```

Original uploads remain immutable.

### 6.2 Archive security

Before parsing:

- Enforce maximum upload size.
- Enforce maximum archive size.
- Enforce maximum uncompressed size.
- Enforce maximum member count.
- Enforce maximum nesting depth.
- Reject absolute paths.
- Reject `..` traversal components.
- Reject symlinks where not required.
- Reject unsupported extensions.
- Enforce parsing timeout.
- Enforce CPU, memory and temporary-disk limits.

Python’s archive documentation warns about path-traversal risks from archive member paths. [web:74]

### 6.3 Discovery artifact

The lightweight inspector produces:

```text
asset_id
archive_type
member_inventory
member_sizes
candidate_formats
sample_headers
candidate_timestamp_fields
candidate_identifier_fields
security_findings
```

It should not read full data or run expensive transforms.

---

## 7. Docker Sandbox

Docker is the recommended simpler alternative to Kubernetes for the current production workload when the deployment is limited to one or a few trusted local servers.

### 7.1 Execution model

```text
Job Manager
  → creates disposable container
  → mounts input read-only
  → mounts output directory
  → disables network by default
  → applies CPU/RAM/disk limits
  → waits for result
  → collects result manifest
  → deletes container
```

### 7.2 Container restrictions

Every parser container should use:

- Non-root execution.
- Read-only root filesystem where possible.
- No privileged mode.
- No host network.
- No Docker socket.
- No arbitrary host mounts.
- Read-only input mount.
- Dedicated output directory.
- Network disabled unless explicitly required.
- CPU limit.
- Memory limit.
- Temporary storage limit.
- Wall-clock timeout.
- Process and file-count limits.

Docker is an isolation layer, not a complete hostile-code security boundary. Do not execute arbitrary user-provided code inside it. Execute only prebuilt, signed parser images.

### 7.3 Parser images

Use small versioned images:

```text
parser-csv:version
parser-xlsx:version
parser-json:version
parser-xml:version
parser-parquet:version
parser-archive:version
```

Each image should contain only the libraries needed for its supported format.

### 7.4 Parser output

The container should write:

```text
output/
├── dataset.parquet
├── schema.json
├── quality_summary.json
├── lineage.json
├── warnings.json
└── parser_result.json
```

The container must not write directly into the final production dataset location. Promotion occurs only after validation.

---

## 8. Apache Data Plane

### 8.1 Apache Arrow

Use Arrow as the internal columnar representation between parser, query and writer components.

```text
Parser output
  → Arrow Table / RecordBatch
  → DataFusion query
  → Arrow result
  → Parquet writer
```

Arrow should be the interchange layer, not a user-facing artifact by itself.

### 8.2 Apache DataFusion

Use DataFusion for:

- Schema inspection.
- CSV/Parquet reading.
- SQL-based projections.
- Joins.
- Aggregations.
- Partition filtering.
- Data profiling scans.
- Conditional compilation operations.

Use parameterized query templates instead of unrestricted SQL generated by an agent.

### 8.3 Apache Parquet

Use Parquet as the canonical internal format for:

- Parsed datasets.
- Compiled datasets.
- Prepared datasets.
- Feature datasets.
- Analytical outputs.

Partition by carefully selected columns such as:

```text
tenant_uid/site_uid/year/month/asset_id
```

Do not partition by extremely high-cardinality fields without measuring the small-file impact.

### 8.4 Apache Kafka

Do not add Kafka solely for file uploads. Add it when you have:

- Multiple plants/sites.
- Concurrent telemetry producers.
- Durable event replay requirements.
- Backpressure between ingestion and processing.
- Multiple downstream consumers.

For initial client-file processing, object storage plus job metadata is simpler.

### 8.5 Apache Beam

Add Beam when ingestion becomes distributed or streaming:

```text
MQTT/Kafka/files
  → Beam pipeline
  → DirectRunner/Flink/Spark/Dataflow runner
  → Arrow/Parquet/Iceberg
```

Do not introduce Beam merely to parse local ZIP uploads.

### 8.6 Apache Iceberg

Add Iceberg when Parquet directories become insufficient because you need:

- Snapshot isolation.
- Schema evolution.
- Time travel.
- Incremental reads.
- Concurrent writers.
- Table-level metadata.

Use Parquet first; add Iceberg when table-management requirements appear.

---

## 9. Data Studio Brain

The Brain should be treated as an API-connected set of reusable services.

```text
Compiler / Parser
        ↓
Data Profiler
        ↓
DAG / Relationship Analysis when needed
        ↓
Recipe Orchestrator
        ↓
Selected execution nodes
```

The route should not invoke every node by default.

### 9.1 Parse-only route

```text
Discovery
  → schema validation
  → chunked parse
  → Arrow
  → Parquet
  → basic quality validation
  → MACHINE_READY package
```

### 9.2 Conditional compilation route

```text
Discovery
  → plan validation
  → DataFusion joins/projections
  → schema harmonization
  → type/time/unit alignment
  → quality validation
  → lineage
  → READY_FOR_PROFILER package
```

### 9.3 Non-ML route

```text
Profiler
  → optional relationship/DAG analysis
  → Recipe Orchestrator
  → PREPARE if required
  → deterministic math/physics analysis
  → Data Service / Visualization
```

Do not call STEM split, model training, model evaluation, Judge or Scorer when the user request is non-ML.

---

## 10. Data Quality with Great Expectations

Use Great Expectations for:

- Versioned expectation suites.
- Client-specific dataset rules.
- Validation results.
- Human-readable data documentation.
- Promotion gates.

Expectation suites should be versioned by:

```text
client
site
asset family
intent type
schema version
```

Example quality categories:

```text
Schema expectations
Timestamp expectations
Required-column expectations
Null-rate expectations
Value-range expectations
Unit expectations
Duplicate expectations
Partition expectations
Row-balance expectations
```

Great Expectations does not decide semantic meaning or model suitability. Those remain AI-ConneX responsibilities.

---

## 11. Orchestration Strategy

### 11.1 Dynamic per-request route

Use:

```text
FastAPI + LangGraph + Job Manager + Docker
```

This path handles:

- User clarification.
- Conditional compilation.
- Per-request plan changes.
- Human approval.
- Job status and resume.

### 11.2 Scheduled/batch route

Use:

```text
Apache Airflow + DockerOperator
```

or, for a future multi-host environment:

```text
Apache Airflow + KubernetesPodOperator
```

Airflow jobs:

- Nightly profiling.
- Historical reprocessing.
- Scheduled data-quality checks.
- Batch Parquet compaction.
- Model retraining.
- Drift evaluation.
- Usage and audit rollups.

Airflow Dynamic Task Mapping is appropriate when a scheduled archive contains an unknown number of files. [web:105]

### 11.3 Scheduling versus execution

```text
Airflow schedules and observes.
Docker executes parser jobs.
Arrow/DataFusion process data.
Parquet stores results.
```

Do not run heavy parsing or model training inside the Airflow scheduler.

---

## 12. CI/CD for Production Client Data

### 12.1 CI gates

Every change should execute:

```text
Ruff / formatting
  → type checking
  → unit tests
  → contract tests
  → archive-security tests
  → plan-validator tests
  → data-quality fixture tests
  → leakage tests
  → tenant-isolation tests
  → parser replay tests
  → container scan
  → SBOM generation
  → signed image build
```

### 12.2 Test data policy

Real client data should not be copied into ordinary CI environments. Use:

- Anonymized client-shaped samples.
- Synthetic data with real schema characteristics.
- Fixed schema fixtures.
- Redacted failure cases.
- Historical replay metadata without sensitive payloads where possible.

Use a separate protected validation environment for approved real-client regression tests.

### 12.3 CD gates

```text
Signed image
  → development
  → ingestion smoke tests
  → malicious archive tests
  → ambiguous-intent tests
  → staging
  → protected replay tests
  → human approval
  → production release
```

Production promotion should remain human-gated. CI/CD can automate evidence generation and staging deployment, but a parser or schema change can alter client data meaning even if the service is technically healthy.

### 12.4 Recommended deployment tools

- Docker Compose for local development and one-server deployment.
- GitHub Actions for CI/CD.
- Argo CD only after Kubernetes is adopted.
- Trivy for image scanning.
- Syft for SBOM generation.
- Cosign for image/artifact signing.
- Vault or cloud KMS for secrets.
- OpenTelemetry, Prometheus and Grafana for observability.

---

## 13. Agent Capability Registry

The agent should call capabilities rather than tools directly.

```text
inspect_archive
create_discovery_artifact
narrow_intent
request_clarification
create_parse_plan
validate_parse_plan
submit_parse_job
get_job_status
read_profile_summary
request_compilation
request_math_analysis
promote_dataset
```

A capability contract should include:

```text
capability_uid
version
input_schema
output_schema
risk_class
side_effect
allowed_autonomy
resource_limits
tenant_scope_required
idempotency_required
approval_requirement
```

Example agent boundary:

```text
Agent
  → typed plan
  → Plan Validator
  → Policy Engine
  → Job Manager
  → Docker parser
  → Output Validator
  → result
```

The agent should never receive:

```text
arbitrary shell execution
arbitrary Python execution
Docker socket
Airflow admin access
Kubernetes cluster-admin
unrestricted SQL
client database credentials
unrestricted network access
```

---

## 14. Production Artifact Package

Every route should produce an artifact package, not just a data file.

```text
machine_ready_package/
├── dataset.parquet
├── schema.json
├── source_inventory.json
├── discovery.json
├── metadata.json
├── quality_summary.json
├── lineage.json
├── plan.json
├── warnings.json
├── quarantine_manifest.json
├── input_hashes.json
└── execution_report.json
```

Recommended statuses:

```text
MACHINE_READY
MACHINE_READY_WITH_WARNINGS
READY_FOR_PROFILER
NEEDS_CLARIFICATION
NEEDS_USER_CORRECTION
QUARANTINED
FAILED
```

`MACHINE_READY` means the dataset has been parsed and structurally validated. `READY_FOR_PROFILER` means the stronger canonical contract is satisfied, including required harmonization and provenance.

---

## 15. Recommended Deployment Sequence

### Phase 1: Current production baseline

Deploy on one or a few servers:

```text
FastAPI
PostgreSQL
MinIO or S3
Docker
Arrow/PyArrow
DataFusion
Parquet
Great Expectations
LangGraph
OpenTelemetry
```

### Phase 2: Scheduled operations

Add:

```text
Apache Airflow
DockerOperator
Airflow Pools
```

Use it for recurring jobs, not conversational routing.

### Phase 3: Scale-out

Add when required:

```text
Kafka
Apache Beam
Apache Iceberg
Kubernetes
KubernetesPodOperator
```

### Phase 4: Heavy distributed ML

Add only when workloads justify it:

```text
Spark
Ray/KubeRay
GPU clusters
KServe/Triton
```

---

## 16. Final Architecture Rule

```text
Agent proposes.
Plan Validator decides.
Docker sandbox executes.
Apache Arrow represents.
DataFusion queries.
Parquet stores.
Great Expectations validates.
Data Profiler describes.
Recipe Orchestrator composes.
Airflow schedules.
PostgreSQL records metadata.
Object storage preserves artifacts.
Human approves production changes.
```

This Apache-first architecture minimizes custom data-processing code while retaining the custom AI-ConneX logic that cannot be delegated to a framework:

- Intent narrowing.
- Conditional compilation.
- Industrial semantics.
- Plan validation.
- Tenant/asset policy.
- Domain constraints.
- Lineage requirements.
- Model and agent governance.
- Production approval.

The result is not a Kubernetes-heavy platform by default. It is an Apache-oriented data plane with Docker-based sandboxing, a LangGraph-driven dynamic control path, Airflow for scheduled operations and a clear migration path to distributed Apache infrastructure when client workload demands it.
