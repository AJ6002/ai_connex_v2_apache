# AI-ConneX Apache Migration — Full End-to-End Execution Plan

**Repository:** `ai_connex_v2_apache`
**Baseline:** Audit dated August 21, 2026
**Structure:** Phase → Sprint → Task → Subtask
**Scope:** Everything from environment installation to production go-live

**Reading rule:** Every task includes a **Pre-Req**, **Do**, and **Verify** step. Do not proceed to the next task until Verify passes. Do not proceed to the next sprint until every task in the current sprint is verified.

---

# PHASE 0 — Environment, Tooling and Baseline Verification

**Goal:** Confirm every engineer/CI runner has an identical, correct toolchain before any code changes. This phase produces zero features; it produces a trustworthy floor.

## Sprint 0.1 — Local Developer Environment

### Task 0.1.1 — Python runtime verification
- **Pre-Req:** None.
- **Subtasks:**
  - Install Python 3.11.x (matches current `python:3.11-slim` base image).
  - Create isolated virtual environment (`.venv311`) per developer machine — do not reuse a shared global environment.
  - Pin `pip`, `setuptools`, `wheel` to known-good versions.
- **Verify:** `python --version` returns 3.11.x. `pip list` shows a clean, minimal environment before installing project dependencies.

### Task 0.1.2 — Node.js runtime verification
- **Pre-Req:** None.
- **Subtasks:**
  - Install Node.js 20.x LTS (recommended over 24.x for frontend stability unless Vite 6/React 19 require newer — confirm against `frontend/package.json` engines field).
  - Install `npm` matching the Node version.
  - Verify `frontend/node_modules` is not committed to git (must be gitignored).
- **Verify:** `node --version`, `npm --version` match repo requirements. `npm ci` (not `npm install`) succeeds from lockfile.

### Task 0.1.3 — Docker Engine verification
- **Pre-Req:** None.
- **Subtasks:**
  - Install Docker Engine v24+.
  - Install Docker Buildx.
  - Confirm daemon supports `--network none`, `--user`, `--memory`, `--cpus` flags (already used by `DockerJobManager`).
  - Confirm non-root Docker group membership for developer accounts (no `sudo docker` dependency in scripts).
- **Verify:** `docker run --rm --network none --user 10001:10001 --memory=1g --cpus=2.0 hello-world` runs successfully.

### Task 0.1.4 — Git and repository access verification
- **Pre-Req:** GitHub account with repo access confirmed.
- **Subtasks:**
  - Clone `ai_connex_v2_apache` fresh (do not reuse an old working copy with drift).
  - Verify remote: `origin -> https://github.com/AJ6002/ai_connex_v2_apache.git`.
  - Verify branch protection rules are visible/enforced on `main`.
- **Verify:** `git remote -v`, `git branch -a`, and a test PR shows required CI checks blocking merge.

## Sprint 0.2 — Dependency Baseline Lock

### Task 0.2.1 — Python dependency lock
- **Pre-Req:** Task 0.1.1 complete.
- **Subtasks:**
  - Freeze current `requirements.txt` into a fully pinned lockfile (exact versions, not `>=`).
  - Add hash-verification (`pip-tools` or `uv` with lockfile hashing).
  - Separate `requirements.txt` (runtime) from `requirements-dev.txt` (test/lint tools: pytest, Ruff, mypy/Pyright).
- **Verify:** `pip install -r requirements.txt` on a clean venv reproduces identical installed versions on two different machines (`pip freeze` diff is empty).

### Task 0.2.2 — Node dependency lock
- **Pre-Req:** Task 0.1.2 complete.
- **Subtasks:**
  - Confirm `package-lock.json` is committed and up to date.
  - Audit for any `"latest"` or unpinned ranges in `frontend/package.json`.
- **Verify:** `npm ci` succeeds with zero lockfile drift warnings.

### Task 0.2.3 — Docker base image pin
- **Pre-Req:** Task 0.1.3 complete.
- **Subtasks:**
  - Pin `python:3.11-slim` to a specific digest (not floating `latest`/`3.11-slim` tag) in `Dockerfile` and all `sandbox/parser-images/*.Dockerfile`.
  - Document the digest in `docs/decisions/base-image-pin.md`.
- **Verify:** `docker inspect` on built images shows the pinned digest matches documentation.

## Sprint 0.3 — Secrets and Configuration Baseline

### Task 0.3.1 — Secrets inventory
- **Pre-Req:** None.
- **Subtasks:**
  - List every secret the system will need at production maturity: DB credentials, object storage keys, GHCR token, MLflow backend store URI, future LLM API keys.
  - Confirm none exist hardcoded in the repo (already stated as clean in audit — re-verify with a secret scanner, e.g., `gitleaks` or `trufflehog`, not just manual `.gitignore` review).
- **Verify:** `gitleaks detect` returns zero findings on full git history, not just current tree.

### Task 0.3.2 — `.env` contract
- **Pre-Req:** Task 0.3.1 complete.
- **Subtasks:**
  - Finalize `.env.example` with every required variable documented (`INTAKE_UPLOAD_DIR`, `LOG_LEVEL`, `PORT`, plus new ones added this phase: `POSTGRES_URL`, `OBJECT_STORAGE_ENDPOINT`, `MLFLOW_TRACKING_URI`).
  - Confirm `.env` is gitignored; confirm `context_log.md` is gitignored (already stated).
- **Verify:** Fresh clone + `.env.example` copy to `.env` + placeholder values allows service boot without crash (fails gracefully on missing real credentials, not on missing variable names).

**Phase 0 Exit Criteria:** Every developer and CI runner can reproduce an identical environment from a fresh clone with zero manual tribal-knowledge steps.

---

# PHASE 1 — Contract and Registry Hardening

**Goal:** The 18 Pydantic contracts and registries are the foundation everything else depends on. Harden them before building more services on top.

## Sprint 1.1 — Contract Completeness Audit

### Task 1.1.1 — Cross-reference contracts against architecture docs
- **Pre-Req:** Phase 0 complete.
- **Subtasks:**
  - Confirm all 16 named contract types in the audit (`agent_spec`, `audit`, `dag`, `dataset`, `deployment`, `discovery`, `feature`, `intent`, `manifest`, `model`, `prepare`, `profile`, `recipe`, `telemetry`, `tenant`, `tool`) exist and are non-empty.
  - Confirm a **Tenant Context** field (`tenant_uid`) is present on every contract that represents a stored resource (dataset, manifest, model, agent, tool call) — this is a hard platform requirement, not optional. [file:19]
  - Confirm `manifest_contract.py` includes references to dataset, profile, DAG, recipe, feature, and optional model/agent refs as the universal join key. [file:21]
- **Verify:** Write a static-analysis script that fails CI if any resource-type contract lacks a `tenant_uid` field.

### Task 1.1.2 — Contract versioning
- **Pre-Req:** Task 1.1.1 complete.
- **Subtasks:**
  - Add a `schema_version` field to every contract.
  - Define N/N-1 backward-compatibility policy for contract changes.
  - Document breaking vs. non-breaking change rules.
- **Verify:** A test that instantiates each contract with a missing `schema_version` fails validation; with it present, passes.

### Task 1.1.3 — Contract test expansion
- **Pre-Req:** Task 1.1.1, 1.1.2 complete.
- **Subtasks:**
  - Expand `tests/contracts/test_contracts.py` beyond the current 7 tests to cover: missing required field rejection, wrong-type rejection, tenant_uid presence, schema_version presence, and one round-trip serialize/deserialize test per contract.
- **Verify:** Test count increases from 7 to (18 contracts × at least 3 new checks each); all green in CI.

## Sprint 1.2 — Registry Hardening

### Task 1.2.1 — Intent Registry validation
- **Pre-Req:** Task 1.1 complete.
- **Subtasks:**
  - Confirm every intent type in `registries/intent/registry.py` (`time_series_forecast`, `anomaly_analysis`, `sensor_visualization`, `historical_sensor_reprocess`, `hourly_sensor_upload`) has: required columns, output contract, and a `requires_model` boolean.
  - Add a `NEEDS_CLARIFICATION` and `BLOCK` fallback route explicitly — the audit shows only positive routes currently defined.
- **Verify:** Unit test sends an unknown/ambiguous intent string and asserts the registry returns `NEEDS_CLARIFICATION`, not a silent default route.

### Task 1.2.2 — Industrial vocabulary and math/physics primitive review
- **Pre-Req:** None (parallel to 1.2.1).
- **Subtasks:**
  - Have a domain engineer (not just a developer) review `registries/industrial_vocabulary/glossary.json` and `registries/math_physics/primitives.json` for correctness against ISO 10816 vibration standards referenced in the audit.
  - Add `owner`, `version`, and `validation_status` metadata fields to each primitive entry.
- **Verify:** Domain sign-off recorded in `docs/decisions/primitives-review.md` with reviewer name and date.

### Task 1.2.3 — Recipe registry contract binding
- **Pre-Req:** Task 1.1.1, 1.2.1 complete.
- **Subtasks:**
  - Confirm `registries/recipes/prepare_recipes.json` entries declare inputs, outputs, and a `destructive_operations: false` safety flag as a first-class field.
- **Verify:** A recipe missing the safety flag fails registry load/validation at startup, not silently at runtime.

**Phase 1 Exit Criteria:** All contracts carry tenant scope and versioning; all registries have explicit fallback/clarification paths; domain math has been signed off by a non-developer reviewer.

---

# PHASE 2 — Data Studio Core Hardening (Intake → Sandbox → Parquet)

**Goal:** Make the already-working ingestion path (Intake → Discovery → DockerJobManager → Parser → Parquet) production-hardened, not just functionally correct.

## Sprint 2.1 — Intake API Hardening

### Task 2.1.1 — Authentication and tenant context injection
- **Pre-Req:** Phase 1 complete.
- **Subtasks:**
  - Add OIDC/OAuth2 authentication middleware to `data-studio/intake/app.py`.
  - Derive `tenant_uid` from verified identity/session — never trust a client-supplied tenant field. [file:19]
  - Reject any request without a resolvable tenant context (`401`/`403`), even in early development, so this habit is baked in from day one.
- **Verify:** Integration test: request with no auth token → rejected. Request with a forged `tenant_uid` in the body but valid auth for a different tenant → server-derived tenant wins, forged value is ignored/logged as an anomaly.

### Task 2.1.2 — Upload size and rate limits
- **Pre-Req:** Task 2.1.1 complete.
- **Subtasks:**
  - Enforce max upload size at the API layer (not just inside `inspector.py`).
  - Add per-tenant rate limiting on `/api/v2/intake/upload` and `/api/v2/intake/intent`.
- **Verify:** Load test exceeding limits returns `413`/`429` cleanly, does not crash the process or exhaust memory.

### Task 2.1.3 — Intent Normalizer confidence handling
- **Pre-Req:** Task 1.2.1 complete.
- **Subtasks:**
  - Add a confidence score to `normalizer.py` output.
  - Route low-confidence classifications to `NEEDS_CLARIFICATION` instead of best-guess routing.
- **Verify:** Ambiguous test prompt (e.g., "do something with my data") returns a clarification response, not a silently wrong intent.

## Sprint 2.2 — Discovery Inspector Hardening

### Task 2.2.1 — Expand security limit configurability
- **Pre-Req:** Task 2.1 complete.
- **Subtasks:**
  - Move the current hardcoded 10x expansion ratio and 500MB limit in `inspector.py` into environment-configurable values per tenant tier.
  - Add: max file count, max nesting depth, max individual file size (currently only total-size and ratio are confirmed in the audit).
- **Verify:** Unit tests: a ZIP with 100,000 tiny files is rejected on file-count grounds even if under the size/ratio limit (classic zip-bomb-by-count variant not yet covered).

### Task 2.2.2 — Symlink and special-file rejection
- **Pre-Req:** Task 2.2.1 complete.
- **Subtasks:**
  - Confirm `inspector.py`'s path-traversal check also explicitly rejects symlink archive members, device files, and non-regular files — the audit only confirms `..`/leading-slash checks.
- **Verify:** Crafted archive with a symlink member is quarantined, not silently followed or extracted.

### Task 2.2.3 — Discovery-only mode (no full read)
- **Pre-Req:** Task 2.2.1, 2.2.2 complete.
- **Subtasks:**
  - Confirm inspector performs metadata-only inspection (names, sizes) without reading full file contents into memory, matching the documented "lightweight discovery" pattern. [file:1]
- **Verify:** Memory profiling test: inspecting a 2GB archive uses bounded memory (not proportional to archive size).

## Sprint 2.3 — Docker Sandbox Hardening

### Task 2.3.1 — Confirm and extend sandbox restrictions
- **Pre-Req:** Task 2.2 complete.
- **Subtasks:**
  - Confirm existing flags: `--network none`, `--user 10001:10001`, `--memory=1g`, `--cpus=2.0`, `-v input:ro` (all present per audit).
  - Add: `--read-only` root filesystem flag with an explicit writable `/tmp` or output-only volume.
  - Add: execution wall-clock timeout with forced kill.
  - Add: `--cap-drop=ALL` and `--security-opt=no-new-privileges`.
- **Verify:** Container attempting to write outside its designated output mount fails. Container exceeding timeout is force-killed and job marked `FAILED_TIMEOUT`, not left hanging.

### Task 2.3.2 — Parser image minimization and pinning
- **Pre-Req:** Task 0.2.3 complete.
- **Subtasks:**
  - Confirm each of `parser-csv.Dockerfile`, `parser-xlsx.Dockerfile`, `parser-parquet.Dockerfile` contains only the libraries needed for its one format (no shared "kitchen sink" image).
  - Pin PyArrow version exactly (audit shows `pyarrow==19.0.1` — confirm this is intentional and tested, not accidental).
- **Verify:** `docker history` on each parser image shows no unused packages (openpyxl only in xlsx image, etc.).

### Task 2.3.3 — Job Manager failure and retry semantics
- **Pre-Req:** Task 2.3.1 complete.
- **Subtasks:**
  - Define explicit job states: `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `FAILED_TIMEOUT`, `QUARANTINED`.
  - Bound retry attempts (max 2–3), no infinite retry loop.
  - Ensure container is always removed after completion regardless of success/failure (`--rm` or explicit cleanup).
- **Verify:** Kill the Docker daemon mid-job in a test environment; confirm the job record transitions to a terminal failure state rather than hanging indefinitely, and no orphan containers remain.

## Sprint 2.4 — Output Validation and Promotion Gate

### Task 2.4.1 — Schema and row-count validation before promotion
- **Pre-Req:** Task 2.3 complete.
- **Subtasks:**
  - Add a validation step after parser output that checks: Parquet is readable, expected columns present, row count within sane bounds, no fully-null critical columns.
  - Introduce this as a distinct `MACHINE_READY` vs `READY_FOR_PROFILER` status distinction, matching the two-tier promotion model. [file:1][file:9]
- **Verify:** A parser that "succeeds" but produces an empty or malformed Parquet file is caught here and marked `FAILED_VALIDATION`, not silently promoted.

### Task 2.4.2 — Lineage and hash recording
- **Pre-Req:** Task 2.4.1 complete.
- **Subtasks:**
  - Confirm SHA-256 input hash, output hash, `asset_id`, and `manifest_id` are all persisted (audit confirms this exists) — extend to also store parser image digest used, for full reproducibility.
- **Verify:** Given a `manifest_id`, a lookup returns the complete chain: input file hash → parser image digest → output file hash → job timestamps.

**Phase 2 Exit Criteria:** A real client-shaped archive can be uploaded, authenticated, tenant-scoped, security-inspected, sandboxed, parsed, validated, and promoted — with every step producing an auditable record and failing safely at every failure point.

---

# PHASE 3 — Apache DataFusion Integration

**Goal:** Move from "PyArrow parses and writes Parquet" to "DataFusion can query the resulting canonical datasets," closing the "PARTIAL" status noted in the audit.

## Sprint 3.1 — DataFusion Installation and Smoke Test

### Task 3.1.1 — Install and pin DataFusion Python bindings
- **Pre-Req:** Phase 2 complete.
- **Subtasks:**
  - Add `datafusion` to `requirements.txt` with a pinned version compatible with the installed `pyarrow==19.0.1`.
  - Verify compatibility matrix between DataFusion's internal Arrow version and the project's PyArrow version — this is the single most common integration break point.
- **Verify:** `python -c "import datafusion; print(datafusion.__version__)"` succeeds in the same environment that runs `pyarrow`.

### Task 3.1.2 — Read-path smoke test
- **Pre-Req:** Task 3.1.1 complete.
- **Subtasks:**
  - Write a minimal script: register a Parquet file produced by `csv_worker.py`, run `SELECT COUNT(*) FROM table`, confirm result matches the known row count from Phase 2 lineage record.
- **Verify:** Row count from DataFusion query exactly matches the row count recorded in the manifest from Task 2.4.2.

## Sprint 3.2 — SQL Query Engine Service

### Task 3.2.1 — Build `data-studio/engine/sql.py`
- **Pre-Req:** Task 3.1.2 complete.
- **Subtasks:**
  - Implement a service that accepts a **parameterized query template** (not arbitrary free-text SQL from an agent) bound to a specific dataset/manifest.
  - Enforce tenant scope as a mandatory `WHERE tenant_uid = :tenant_uid` clause injected server-side, never client-supplied.
- **Verify:** Attempt to query without a tenant filter is rejected at the service layer before reaching DataFusion. Attempt to inject a different tenant's filter is overridden by the server-derived value.

### Task 3.2.2 — Profiling queries on DataFusion
- **Pre-Req:** Task 3.2.1 complete.
- **Subtasks:**
  - Implement the first three Profiler queries using DataFusion: null-rate per column, min/max/mean for numeric columns, distinct-count for candidate identifier columns.
- **Verify:** Results match a manual pandas/Polars calculation on the same fixture dataset within floating-point tolerance.

### Task 3.2.3 — Join/compilation queries on DataFusion
- **Pre-Req:** Task 3.2.2 complete.
- **Subtasks:**
  - Implement a controlled join operation (e.g., machine_id + timestamp join between two Parquet datasets) with cardinality estimation before execution to prevent many-to-many explosion. [file:1]
- **Verify:** A crafted many-to-many join test case (100k × 50k on a non-unique key) is rejected or flagged before full execution, not run to completion and then discovered as an OOM crash.

**Phase 3 Exit Criteria:** DataFusion is a tested, tenant-scoped, parameterized query layer over Parquet — not an unrestricted SQL surface, and not merely an unused import.

---

# PHASE 4 — Data Studio Brain: Profiler, PREPARE, Recipe/DAG Rewrite

**Goal:** Replace the legacy Pandas/Flask Profiler, Compiler, and PREPARE logic (marked HIGH domain quality / LOW infra quality in the audit) with Arrow/DataFusion-native implementations, porting only the domain logic.

## Sprint 4.1 — Profiler Rewrite

### Task 4.1.1 — Extract domain logic from legacy profiler
- **Pre-Req:** Phase 3 complete.
- **Subtasks:**
  - Read `archive_legacy/services/1_dataset_profiler/` and extract the **business rules** only (missing-value ratio thresholds, cardinality thresholds, semantic-type heuristics) — do not port the Flask routing or Pandas execution code.
  - Document extracted rules in `docs/decisions/profiler-rules-extracted.md`.
- **Verify:** A domain reviewer confirms the extracted rule list matches legacy behavior for at least 5 known historical datasets.

### Task 4.1.2 — Implement `data-studio/profiler/` on DataFusion/Arrow
- **Pre-Req:** Task 4.1.1, Task 3.2.2 complete.
- **Subtasks:**
  - Implement structural profile (row/column counts, types, schema hash).
  - Implement statistical profile (numeric summary stats, categorical frequency).
  - Implement temporal profile (timestamp range, sampling interval, gap detection).
  - Implement semantic profile using the extracted rules from 4.1.1.
  - Emit `manifest-UID.json` combining intent + compiler facts + profile facts, matching the documented contract. [file:11]
- **Verify:** Run against the same 5 historical datasets used in 4.1.1; profiler output matches legacy output within documented tolerance for every metric.

### Task 4.1.3 — Profile scoring and readiness state
- **Pre-Req:** Task 4.1.2 complete.
- **Subtasks:**
  - Implement the weighted profile score (quality, completeness, structural validity, temporal integrity, semantic confidence) and map to `READY` / `CONDITIONALLY_READY` / `REVIEW_REQUIRED` / `NOT_READY`. [file:11]
- **Verify:** A deliberately corrupted fixture (40% nulls in a required column) produces `NOT_READY`, not a silently passing score.

## Sprint 4.2 — PREPARE Rewrite

### Task 4.2.1 — Extract domain logic from legacy PREPARE
- **Pre-Req:** Phase 3 complete (parallel to Sprint 4.1).
- **Subtasks:**
  - Extract outlier-handling rules and sensor-interpolation logic from `archive_legacy/services/4_prepare/`.
  - Explicitly flag any rule that silently deletes data — these must become quarantine actions, not deletions, per the "never clean blindly" principle. [file:13]
- **Verify:** Domain reviewer confirms no extracted rule performs silent deletion; all destructive-seeming rules are reclassified as quarantine + reason code.

### Task 4.2.2 — Implement `data-studio/prepare/` as PyArrow compute kernel
- **Pre-Req:** Task 4.2.1, Task 4.1.2 complete.
- **Subtasks:**
  - Implement schema validation against manifest.
  - Implement missing-value handling per column-role policy (numeric short-gap interpolation, target-column never-impute rule).
  - Implement duplicate handling (exact vs. key vs. legitimate-repeat classification).
  - Implement unit normalization with a recorded conversion rule per column.
  - Implement quarantine output with reason codes.
  - Add dry-run mode that reports intended changes without writing output. [file:13]
- **Verify:** Dry-run on a 10M-row fixture reports expected quarantine/modification counts; actual run matches dry-run counts exactly.

### Task 4.2.3 — Before/after accounting and lineage
- **Pre-Req:** Task 4.2.2 complete.
- **Subtasks:**
  - Emit `prepare_report.json` with input_rows, output_rows, quarantined_rows, modified_rows, nulls_before/after, duplicates_before/after.
- **Verify:** Sum of output_rows + quarantined_rows + dropped_rows equals input_rows exactly for every test run (row-conservation invariant).

## Sprint 4.3 — DAG/Recipe Domain Logic Port

### Task 4.3.1 — Port DAG family/algorithm registry
- **Pre-Req:** Phase 1 (registries) complete.
- **Subtasks:**
  - Migrate the ISO vibration formulas and DAG representation logic from `archive_legacy/services/2_dag/` and `3_recipe_orchestrator/` into `registries/recipes/` and a new `orchestration/dag/` registry structure.
  - Preserve Family ID / DAG ID structure if the legacy system used a similar taxonomy (classification, regression, anomaly detection, time-series, etc., per the documented 10-family model). [file:8]
- **Verify:** Every ported DAG entry has a unique ID, and a registry-validation script rejects duplicate IDs or entries missing a family assignment.

### Task 4.3.2 — Recipe compatibility engine
- **Pre-Req:** Task 4.3.1, Task 4.1.3 complete.
- **Subtasks:**
  - Implement the eligibility check: given a profile and intent, filter DAG candidates by hard constraints (target present, modality match) then rank by soft criteria.
- **Verify:** Test with a profile lacking a required target column: assert zero DAG candidates returned with a clear `NO_COMPATIBLE_DAG` reason, not a fallback guess.

**Phase 4 Exit Criteria:** Profiler, PREPARE, and DAG/Recipe logic run natively on Arrow/DataFusion with zero dependency on legacy Pandas/Flask code, and produce output matching legacy behavior on historical reference datasets.

---

# PHASE 5 — ML Studio Rewrite (Feature Engineering → Split → Train → Evaluate → ONNX)

**Goal:** Port the HIGH-quality domain logic (feature engineering, leakage-free split, AutoML training, evaluation, ONNX export) into clean modular ML Studio packages with MLflow tracking.

## Sprint 5.1 — Feature Engineering Port

### Task 5.1.1 — Install and pin ML dependencies
- **Pre-Req:** Phase 4 complete.
- **Subtasks:**
  - Add `scikit-learn`, `mlflow`, `onnx`, `onnxruntime`, and (if approved after review) `tsfresh` to a new `ml-studio/requirements.txt` separate from the Data Studio requirements — these are heavier and should not bloat the parser sandbox images.
- **Verify:** `pip install -r ml-studio/requirements.txt` succeeds in a dedicated ML Studio virtual environment, isolated from `data-studio/`.

### Task 5.1.2 — Port lag/rolling/FFT feature primitives
- **Pre-Req:** Task 5.1.1 complete.
- **Subtasks:**
  - Extract `rolling_mean`, `fft_spectrum`, `lag_features` logic from `archive_legacy/services/5_feature_engineering/` into `ml-studio/feature-engineering/primitives/`.
  - Enforce point-in-time correctness explicitly: every feature must declare its allowed observation lag relative to the prediction timestamp. [file:12]
- **Verify:** A leakage test that constructs a feature using a future timestamp is rejected by an automated leakage-detection unit test, not caught only by manual review.

### Task 5.1.3 — Feature registry and versioning
- **Pre-Req:** Task 5.1.2 complete.
- **Subtasks:**
  - Register each ported primitive with a stable feature ID, version, entity key, and leakage classification (deterministic vs. learned).
- **Verify:** Two runs with identical input and config produce byte-identical feature output hashes (reproducibility test).

## Sprint 5.2 — Split Engine Port

### Task 5.2.1 — Port leakage-free temporal split
- **Pre-Req:** Task 5.1.3 complete.
- **Subtasks:**
  - Port the legacy split logic (marked HIGH infra quality already, per audit — this is a clean port, not a rewrite) into `ml-studio/split/`.
  - Confirm chronological split for time-series, group-aware split for multi-entity data.
- **Verify:** A split-validation test confirms zero timestamp overlap between train and test partitions for a time-series fixture.

## Sprint 5.3 — Training Rewrite

### Task 5.3.1 — Rebuild AutoML trainer with MLflow tracking
- **Pre-Req:** Task 5.2.1 complete.
- **Subtasks:**
  - Rebuild the LightGBM/XGBoost/Random Forest training loop from `archive_legacy/services/7_train/` as a clean module in `ml-studio/training/`.
  - Wrap every training run in an MLflow experiment run: log parameters, metrics, dataset hash, feature version, code version.
- **Verify:** MLflow UI shows a complete experiment record for a test training run, traceable back to the exact manifest UID and feature version used.

### Task 5.3.2 — One-loop multi-candidate training
- **Pre-Req:** Task 5.3.1 complete.
- **Subtasks:**
  - Implement the STEM one-loop pattern: for each candidate DAG/family, split → train all suggested models → evaluate — not just a single best-guess model. [file:18]
- **Verify:** A test run with 2 DAG candidates × 2 families × 2 models produces exactly 8 tracked MLflow runs, each linked to its DAG/family/model identity.

## Sprint 5.4 — Evaluation Port

### Task 5.4.1 — Port evaluator logic cleanly
- **Pre-Req:** Task 5.3.2 complete.
- **Subtasks:**
  - Port RMSE/MAE/R²/confusion-matrix logic from `archive_legacy/services/8_evaluate/` into `ml-studio/evaluation/` (already HIGH quality on both axes per audit — minimal rewrite needed).
  - Predeclare metrics **before** evaluation runs, not after seeing results (prevents metric cherry-picking). [file:16]
- **Verify:** Metric configuration is loaded and locked before the first model is evaluated; a code-review check confirms no evaluation code branch can alter the metric list mid-run.

### Task 5.4.2 — Judge and Scorer implementation
- **Pre-Req:** Task 5.4.1 complete.
- **Subtasks:**
  - Implement deterministic Scorer (weighted formula) and a rules-based or LLM-assisted Judge that explains trade-offs but does not override the Scorer's hard-constraint filtering.
- **Verify:** Given identical evaluation results, Scorer output is bit-for-bit reproducible across repeated runs (no hidden randomness in scoring weights).

## Sprint 5.5 — ONNX Export Rewrite

### Task 5.5.1 — Standalone ONNX export worker
- **Pre-Req:** Task 5.4.2 complete.
- **Subtasks:**
  - Rebuild ONNX conversion from `archive_legacy/services/9_deploy_monitor/` as a standalone containerized worker in `ml-studio/serving/`, following the same Docker sandbox pattern established in Phase 2 (non-root, resource-limited).
- **Verify:** A trained model converts to ONNX and produces numerically equivalent predictions (within tolerance) compared to the original scikit-learn/LightGBM model on a held-out test batch.

**Phase 5 Exit Criteria:** A dataset can flow from Data Studio's `READY_FOR_PROFILER` output through feature engineering, leakage-free split, multi-candidate training with MLflow tracking, evaluation, Judge/Scorer selection, and ONNX export — fully traceable end to end.

---

# PHASE 6 — Frontend Re-Wiring

**Goal:** Connect the already-built 17-view React shell to the real v2 FastAPI/DataFusion/ML Studio backend, replacing mock/v1 endpoint calls.

## Sprint 6.1 — API Client Rewiring

### Task 6.1.1 — Audit current API client calls
- **Pre-Req:** Phase 2 complete (Intake API stable).
- **Subtasks:**
  - Grep `frontend/src/` for all hardcoded `http://localhost:` and legacy v1 port references.
  - Produce a checklist of every component needing rewiring (`JaneChat.tsx`, `UploadModal.tsx`, `MLStudio.tsx` per audit's PARTIAL status).
- **Verify:** Checklist reviewed and each item has a target v2 endpoint assigned before coding begins.

### Task 6.1.2 — Rewire Upload Modal
- **Pre-Req:** Task 6.1.1 complete.
- **Subtasks:**
  - Point `UploadModal.tsx` to `/api/v2/intake/upload`.
  - Handle new response contract (job_uid, status polling or SSE subscription).
- **Verify:** Manual upload through the UI produces a visible job status transition matching backend job states from Task 2.3.3.

### Task 6.1.3 — Rewire Jane Chat with SSE
- **Pre-Req:** Task 6.1.1 complete.
- **Subtasks:**
  - Implement SSE client binding to `/api/v2/intake/intent`.
  - Separate event types: `chat.token`, `intent.updated`, `clarification.required` — do not bundle chat text and state signals into one blob.
- **Verify:** A clarification-required response from Task 2.1.3 renders as a distinct UI prompt, not appended as plain chat text.

### Task 6.1.4 — Rewire ML Studio view
- **Pre-Req:** Task 6.1.1 complete, Phase 5 Sprint 5.3 complete.
- **Subtasks:**
  - Connect model-family selection UI to the real DAG/family registry from Task 4.3.1.
  - Connect training-start action to a confirmation gate (expensive action) before submitting to `ml-studio/training/`.
- **Verify:** Attempting to start training without confirming shows a blocking "Are you sure?" dialog; confirming triggers a real MLflow-tracked run visible in Task 5.3.1's tracking UI.

## Sprint 6.2 — Stage Tabs and Two-Axis State Wiring

### Task 6.2.1 — Wire Stage Tabs to real backend events
- **Pre-Req:** Task 6.1.3 complete.
- **Subtasks:**
  - Confirm `StageTabs.tsx` unlocks a stage only upon receiving an authorized `stage.ready` SSE event with a validated artifact reference — not on optimistic client-side assumption.
- **Verify:** Kill the backend mid-pipeline; confirm the frontend stage tab remains locked rather than optimistically unlocking.

### Task 6.2.2 — Implement persistent workspace state (Axis A)
- **Pre-Req:** Task 6.2.1 complete, Phase 7 Sprint 7.1 (PostgreSQL) complete.
- **Subtasks:**
  - Move capability-unlock state out of frontend memory into backend-persisted workspace records.
  - On page refresh/reconnect, frontend re-fetches Axis A state rather than resetting to locked.
- **Verify:** Refresh the browser mid-workflow; confirm previously unlocked stages remain unlocked without re-running the pipeline.

**Phase 6 Exit Criteria:** All 17 frontend views communicate exclusively with the v2 backend; no mock/v1 endpoint references remain; state survives reconnects.

---

# PHASE 7 — Persistent Storage Migration (SQLite → PostgreSQL, Object Storage)

**Goal:** Replace the lightweight SQLite session tracker with production-grade PostgreSQL and add S3/MinIO-compatible object storage, per the audit's explicit "REPLACE WITH POSTGRES" decision.

## Sprint 7.1 — PostgreSQL Setup

### Task 7.1.1 — Install and configure PostgreSQL
- **Pre-Req:** Phase 0 complete.
- **Subtasks:**
  - Provision PostgreSQL 16.x (local Docker container for dev, managed instance for production).
  - Create database schema with Row-Level Security enabled on every tenant-scoped table. [file:19]
- **Verify:** `SELECT * FROM datasets WHERE tenant_uid != current_setting('app.current_tenant')` returns zero rows when RLS is active, confirming isolation.

### Task 7.1.2 — Migration from SQLite tracker
- **Pre-Req:** Task 7.1.1 complete.
- **Subtasks:**
  - Design schema for job records, manifests, lineage, tenant registry (replacing `services/sqlite_tracker.py`).
  - Write a one-time migration script for any dev-environment SQLite data worth preserving (likely none for production — confirm with team before writing migration code).
- **Verify:** New job records write successfully to PostgreSQL; SQLite tracker is fully decommissioned from the active code path.

### Task 7.1.3 — Connection pooling and health checks
- **Pre-Req:** Task 7.1.2 complete.
- **Subtasks:**
  - Add connection pooling (e.g., `asyncpg` pool) to FastAPI services.
  - Add a `/health` endpoint that verifies live DB connectivity.
- **Verify:** Restart the PostgreSQL container; confirm the API's `/health` endpoint correctly reports degraded status and recovers automatically once the DB returns.

## Sprint 7.2 — Object Storage Setup

### Task 7.2.1 — MinIO installation for local/on-prem
- **Pre-Req:** Task 0.1.3 complete.
- **Subtasks:**
  - Deploy MinIO as a Docker service for raw uploads, Parquet outputs, and reports.
  - Define tenant-prefixed bucket/path convention: `tenant/site/studio/resource_type/resource_uid/`. [file:19]
- **Verify:** Two different tenants' uploads are stored under separate prefixes; a test attempting to read another tenant's prefix via the API is rejected.

### Task 7.2.2 — Replace local filesystem storage
- **Pre-Req:** Task 7.2.1 complete.
- **Subtasks:**
  - Add an S3-compatible storage driver to replace direct writes to `services/workspace_data/`.
  - Keep local filesystem as a fallback only for single-node dev mode, clearly flagged in config.
- **Verify:** Job Manager writes Parquet output to MinIO instead of local disk in a staging environment; retrieval via signed URL succeeds.

**Phase 7 Exit Criteria:** PostgreSQL with RLS is the system of record for all metadata; MinIO (or equivalent) is the system of record for all artifacts; SQLite and local-disk-only storage are fully retired from production paths.

---

# PHASE 8 — Knowledge Base and RAG Rebuild

**Goal:** Preserve domain knowledge content while rebuilding the retrieval pipeline cleanly, per the audit's stated strategy.

## Sprint 8.1 — Content Preservation

### Task 8.1.1 — Migrate raw domain documents
- **Pre-Req:** None (can run in parallel to earlier phases).
- **Subtasks:**
  - Copy ISO 10816 vibration standards, turbofan predictive-maintenance specs, and vocabulary glossaries from `archive_legacy/*_KB_raw_data/` into `knowledge/domain_docs/`.
  - Attach metadata per `knowledge/metadata/schema.json`: owner, version, effective dates, approval status.
- **Verify:** Every migrated document has complete metadata; a validation script rejects any document missing required metadata fields.

## Sprint 8.2 — Clean Vector Pipeline Rebuild

### Task 8.2.1 — Fresh Qdrant instance
- **Pre-Req:** Task 8.1.1 complete.
- **Subtasks:**
  - Deploy a new, clean Qdrant instance — explicitly do not reuse `archive_legacy/.mem0_qdrant` (marked DROP/rebuild in audit).
  - Define tenant-scoped collection or metadata-filter strategy.
- **Verify:** A cross-tenant retrieval test confirms Tenant A's query cannot return Tenant B's chunked documents.

### Task 8.2.2 — Arrow-based chunking pipeline
- **Pre-Req:** Task 8.2.1 complete, Phase 3 complete.
- **Subtasks:**
  - Build the ingestion pipeline using PyArrow for chunking/metadata handling as planned in the audit's migration strategy.
- **Verify:** Re-ingesting the same document twice does not create duplicate vector entries (idempotent ingestion).

**Phase 8 Exit Criteria:** Domain knowledge is preserved with full metadata; retrieval is tenant-isolated and running on a fresh, clean vector store.

---

# PHASE 9 — Apache Airflow Scheduled Orchestration

**Goal:** Add the currently MISSING Airflow layer for scheduled/batch workloads only — not for dynamic per-request routing.

## Sprint 9.1 — Airflow Installation

### Task 9.1.1 — Deploy Airflow via Docker Compose
- **Pre-Req:** Phase 7 (PostgreSQL) complete — Airflow needs its own metadata DB, can share the PostgreSQL instance with a separate schema.
- **Subtasks:**
  - Deploy Airflow scheduler, webserver, and a Celery/Local executor via Docker Compose.
  - Configure Airflow's own metadata database (separate schema from application data).
- **Verify:** Airflow UI is reachable; a trivial "hello world" DAG runs successfully end to end.

### Task 9.1.2 — DockerOperator integration
- **Pre-Req:** Task 9.1.1 complete, Phase 2 (parser images) complete.
- **Subtasks:**
  - Configure Airflow's `DockerOperator` to invoke the existing `parser-csv`/`parser-xlsx`/`parser-parquet` images with the same security flags already established in `DockerJobManager` (Task 2.3.1) — do not create a second, less-secure execution path.
- **Verify:** An Airflow-triggered parser run produces output identical to a direct `DockerJobManager`-triggered run on the same input file.

## Sprint 9.2 — First Scheduled Workflows

### Task 9.2.1 — Nightly reprocessing DAG
- **Pre-Req:** Task 9.1.2 complete, Phase 4 (Profiler) complete.
- **Subtasks:**
  - Build a DAG: scan for unprocessed/flagged datasets → re-run Profiler → update manifest.
- **Verify:** Scheduling the DAG for a test window produces updated manifests without manual intervention, and Airflow's UI shows successful task history.

### Task 9.2.2 — Scheduled model drift check
- **Pre-Req:** Task 9.2.1 complete, Phase 5 complete.
- **Subtasks:**
  - Build a DAG: pull recent production inference data → compare distribution against training baseline → alert if drift threshold exceeded.
- **Verify:** Injecting an artificially shifted test dataset triggers the drift alert path; a normal dataset does not.

**Phase 9 Exit Criteria:** Airflow handles only scheduled/batch workloads using the same security-hardened execution primitives as the real-time path; dynamic conversational routing remains outside Airflow.

---

# PHASE 10 — Data Quality Layer (Great Expectations)

**Goal:** Add the currently MISSING Great Expectations validation layer at the promotion gate.

## Sprint 10.1 — Installation and First Suites

### Task 10.1.1 — Install and configure Great Expectations
- **Pre-Req:** Phase 2 complete.
- **Subtasks:**
  - Add `great_expectations` to `data-studio/requirements.txt`.
  - Initialize a GX project pointed at the Parquet output directory/object storage location.
- **Verify:** GX CLI can successfully connect to and profile a sample Parquet dataset.

### Task 10.1.2 — First expectation suite (hourly sensor upload)
- **Pre-Req:** Task 10.1.1 complete.
- **Subtasks:**
  - Build one suite for the `hourly_sensor_upload` intent type: required columns exist, timestamp valid, sensor_id not null, reading numeric, duplicate rate under threshold.
- **Verify:** Running the suite against a known-good fixture passes; against a deliberately broken fixture (missing column), it fails with a clear, specific report.

## Sprint 10.2 — Promotion Gate Integration

### Task 10.2.1 — Wire GX into the promotion step
- **Pre-Req:** Task 10.1.2 complete, Task 2.4.1 complete.
- **Subtasks:**
  - Insert the GX validation run between parser output and the `MACHINE_READY`/`READY_FOR_PROFILER` promotion decision from Task 2.4.1.
  - Store the validation report as a permanent artifact alongside the manifest.
- **Verify:** A dataset failing GX validation is blocked from promotion and visibly marked `NEEDS_REVIEW`, with the GX report attached and retrievable via the manifest.

**Phase 10 Exit Criteria:** No dataset reaches `READY_FOR_PROFILER` status without passing a versioned, auditable Great Expectations suite appropriate to its intent type.

---

# PHASE 11 — Security Hardening and Compliance Pass

**Goal:** Formal security review before any real client data touches the system.

## Sprint 11.1 — Penetration and Boundary Testing

### Task 11.1.1 — Cross-tenant attack suite
- **Pre-Req:** Phase 7 (PostgreSQL RLS), Phase 8 (Qdrant tenant isolation) complete.
- **Subtasks:**
  - Implement the full cross-tenant test suite: dataset access, cache poisoning, IDOR, vector leakage, graph leakage (if applicable), telemetry leakage. [file:19]
- **Verify:** All cross-tenant attack attempts return `403`/`404`/empty results; zero successful boundary crossings.

### Task 11.1.2 — Archive attack replay
- **Pre-Req:** Phase 2 complete.
- **Subtasks:**
  - Replay Zip Slip, zip bomb (by ratio and by file count), symlink, and corrupt-archive test cases against the production-configured Discovery Inspector.
- **Verify:** Every attack fixture is rejected or quarantined; none crash the service or exhaust resources.

## Sprint 11.2 — Supply Chain and Secrets

### Task 11.2.1 — Full dependency vulnerability sweep
- **Pre-Req:** Phase 0–10 dependencies finalized.
- **Subtasks:**
  - Run Trivy (already in CI) plus a Python-specific scanner (`pip-audit`) and Node-specific scanner (`npm audit`) across all three dependency trees.
- **Verify:** Zero CRITICAL findings; documented risk acceptance for any HIGH findings that cannot be immediately remediated.

### Task 11.2.2 — Secrets rotation drill
- **Pre-Req:** Task 0.3 complete, production secrets provisioned.
- **Subtasks:**
  - Rotate one real credential (e.g., GHCR token) end to end and confirm all dependent services pick up the new value without a full redeploy from scratch.
- **Verify:** Rotation completes with zero downtime and zero hardcoded-value discovery.

**Phase 11 Exit Criteria:** Independent security review (internal or external) signs off before real client data is processed in the staging/production environment.

---

# PHASE 12 — Staging Deployment and Client-Data Readiness

**Goal:** Deploy the full stack to a staging environment and validate with real client-shaped (not necessarily real client) data before go-live.

## Sprint 12.1 — Staging Environment Provisioning

### Task 12.1.1 — Docker Compose staging stack
- **Pre-Req:** Phases 0–11 complete.
- **Subtasks:**
  - Assemble a full Docker Compose stack: API, PostgreSQL, MinIO, Qdrant, Airflow, frontend, all parser images.
  - Deploy to a staging host separate from developer machines.
- **Verify:** Full stack boots cleanly from a single `docker-compose up` on a fresh staging host with no manual patching.

### Task 12.1.2 — End-to-end smoke test
- **Pre-Req:** Task 12.1.1 complete.
- **Subtasks:**
  - Run one complete flow: upload → intake → intent → discovery → sandbox parse → Parquet → GX validation → Profiler → PREPARE → Feature Engineering → training → ONNX export → frontend display.
- **Verify:** Every stage produces its expected artifact and status transition, visible end to end in the frontend.

## Sprint 12.2 — Real Client-Shaped Data Validation

### Task 12.2.1 — Protected replay environment
- **Pre-Req:** Task 12.1.2 complete.
- **Subtasks:**
  - Set up an isolated, access-controlled environment for testing against real (or realistically anonymized) client data — never in the standard CI pipeline.
- **Verify:** Access to this environment is logged and restricted to named approvers.

### Task 12.2.2 — Client data dry run
- **Pre-Req:** Task 12.2.1 complete.
- **Subtasks:**
  - Run the full pipeline against one real client dataset in the protected environment.
  - Compare output against any available legacy-system output for the same dataset (if one exists) as a sanity check.
- **Verify:** Domain expert signs off that output semantics match expectations; discrepancies are documented and resolved before proceeding.

**Phase 12 Exit Criteria:** Staging environment has processed at least one real client dataset successfully with documented sign-off.

---

# PHASE 13 — Production Go-Live

**Goal:** Controlled, human-gated production release.

## Sprint 13.1 — Production Provisioning

### Task 13.1.1 — Production infrastructure setup
- **Pre-Req:** Phase 12 complete.
- **Subtasks:**
  - Provision production PostgreSQL, object storage, and container hosts (or Kubernetes only if genuinely required by this point — Docker Compose may still be sufficient per earlier guidance).
  - Configure production secrets in a secret manager (Vault/KMS/cloud-native equivalent).
- **Verify:** Production environment passes the same smoke test suite from Task 12.1.2.

### Task 13.1.2 — Human-gated deployment
- **Pre-Req:** Task 13.1.1 complete.
- **Subtasks:**
  - Confirm CI/CD auto-deploys only to staging; production promotion requires an explicit human approval action (merge to a protected production branch or manual pipeline approval step).
- **Verify:** Attempting to push directly to production without the approval gate is blocked by CI/CD configuration, not merely by convention.

## Sprint 13.2 — Go-Live and Immediate Post-Launch

### Task 13.2.1 — Production go-live
- **Pre-Req:** Task 13.1.2 complete, all prior phase exit criteria met.
- **Subtasks:**
  - Execute the approved production deployment.
  - Monitor dashboards (OpenTelemetry/Prometheus/Grafana if provisioned, or at minimum structured logs) for the first 24–48 hours actively.
- **Verify:** Zero unplanned rollbacks in the first 48 hours; all health checks green.

### Task 13.2.2 — Post-launch retrospective
- **Pre-Req:** Task 13.2.1 complete, minimum 1 week of production operation.
- **Subtasks:**
  - Document what worked, what required hotfixes, and update `docs/decisions/` accordingly.
  - Feed lessons learned into the backlog for Phase 14 (future Kafka/Beam/Iceberg/Kubernetes expansion — deferred until genuinely required).
- **Verify:** Retrospective document reviewed and signed off by the team.

**Phase 13 Exit Criteria:** System is live in production, processing real client data, with a documented, human-approved deployment history and a stable first week of operation.

---

# Master Phase Summary Table

| Phase | Focus | Hard Dependency | Exit Signal |
|---|---|---|---|
| 0 | Environment & tooling baseline | None | Reproducible clean-clone setup |
| 1 | Contract & registry hardening | Phase 0 | Tenant scope + versioning on all contracts |
| 2 | Data Studio core hardening | Phase 1 | Full ingest→sandbox→Parquet path is audited-safe |
| 3 | DataFusion integration | Phase 2 | Tenant-scoped SQL query layer working |
| 4 | Brain rewrite (Profiler/PREPARE/DAG) | Phase 3 | Legacy domain logic ported, infra rewritten |
| 5 | ML Studio rewrite | Phase 4 | End-to-end training with MLflow + ONNX |
| 6 | Frontend re-wiring | Phase 2 (parallel-capable) | All views hit real v2 backend |
| 7 | Storage migration | Phase 0 (parallel-capable) | PostgreSQL RLS + MinIO live |
| 8 | Knowledge Base rebuild | Phase 0 (parallel-capable) | Clean, tenant-isolated RAG |
| 9 | Airflow orchestration | Phase 2, 7 | Scheduled DAGs using same security primitives |
| 10 | Data quality (Great Expectations) | Phase 2 | GX gate blocks bad promotions |
| 11 | Security hardening | Phases 2, 7, 8 | Zero cross-tenant leaks; clean scans |
| 12 | Staging + client-data validation | All prior | Real dataset processed and signed off |
| 13 | Production go-live | Phase 12 | Live, stable, human-approved release |

**Parallelization note:** Phases 6, 7, 8 can run concurrently with Phases 3–5 since they depend primarily on Phase 0/2, not on each other. Do not parallelize Phase 4 and Phase 5 — Phase 5 (ML Studio) structurally depends on Phase 4's Profiler/PREPARE/DAG output contracts.

**Non-negotiable rule carried through every phase:** No task is "done" because code was written — it is "done" only when its Verify step passes with evidence, matching the project's existing pattern of `7/7 passing` contract tests rather than unverified claims.
