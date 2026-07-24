# Migration Plan v2: Monolith → Extensible Plugin Pipeline Architecture

Migrate `aiconnex_zip_compiler/` from a monolithic converter codebase to a **decoupled, multi-stage plugin registry** with deterministic selection, immutable run snapshots, and agent-as-plugin-releaser model.

---

## User Review Required

> [!IMPORTANT]
> This is a **full branch-level refactor** of `feature/agentic-scout-compiler`. Every existing converter, joiner, and discovery module will be decomposed into independent, testable plugin files. The `compiler.py` core will shrink from 222 lines of orchestration logic to a thin pipeline executor that queries a `PluginRegistry`.

> [!WARNING]
> The current 8/8 regression test suite must remain green throughout migration. We will use a **strangler-fig pattern**: new plugins coexist alongside old code until each stage is validated, then old code is removed.

---

## 1. The Problem with the Current Monolith

Today, the compiler is structured as one large orchestrator ([compiler.py](file:///x:/TAS/AICONNEX/aiconnex_zip_compiler/compiler.py)) that directly imports and calls:
- [discovery.py](file:///x:/TAS/AICONNEX/aiconnex_zip_compiler/discovery.py) (312 lines — ZIP walking, CSV profiling, role assignment)
- [schema_mapper.py](file:///x:/TAS/AICONNEX/aiconnex_zip_compiler/schema_mapper.py) (~100 lines — timestamp/column normalization)
- [relational_joiner.py](file:///x:/TAS/AICONNEX/aiconnex_zip_compiler/relational_joiner.py) (~200 lines — fact/dim joins)
- [excel_converter.py](file:///x:/TAS/AICONNEX/aiconnex_zip_compiler/excel_converter.py) (~200 lines — SCADA multi-header Excel)
- [hdf5_converter.py](file:///x:/TAS/AICONNEX/aiconnex_zip_compiler/hdf5_converter.py) (~100 lines — HDF5 telemetry)
- [mat_converter.py](file:///x:/TAS/AICONNEX/aiconnex_zip_compiler/mat_converter.py) (~100 lines — MATLAB struct extraction)
- [snapshot_aggregator.py](file:///x:/TAS/AICONNEX/aiconnex_zip_compiler/snapshot_aggregator.py) (173 lines — vibration signal feature harvesting)

**When the Scout Agent detects an unknown format**, it currently must either:
- Edit `compiler.py` itself (high blast radius), or
- Drop a file into `custom_converters/` that is manually wired in.

Neither approach scales. Every new dataset format means touching shared core code.

---

## 2. The Four Independent Axes of Ingestion

Every dataset the compiler will encounter can be described along **four orthogonal axes**:

| Axis | Examples | Why It Matters |
|:---|:---|:---|
| **Container** | `.zip`, directory, single file, nested archive | How to *extract* and *walk* the raw input |
| **Physical Format** | `.csv`, `.xlsx`, `.mat`, `.h5`, `.parquet`, `.txt`, `.json`, `.tdms` | How to *read bytes* into DataFrames |
| **Schema Shape** | Flat table, multi-table relational, hierarchical struct, time-series snapshots | How to *assemble* multiple parsed tables into one logical dataset |
| **Transformation Need** | Parse only, parse + join, parse + aggregate, parse + feature-harvest | What *post-parse processing* is needed before handoff |

The plugin system must ask **"what ingestion pattern is this?"** — not just "what file type is this?"

---

## 3. The 5-Stage Plugin Pipeline

```
   Raw Archive / Dataset Input
              │
              ▼
   ┌──────────────────────────────┐
   │ Stage 1: DISCOVERY PLUGINS   │   Walk containers, classify layout & file inventory
   └──────────┬───────────────────┘
              ▼
   ┌──────────────────────────────┐
   │ Stage 2: PARSER PLUGINS      │   Convert raw bytes → DataFrames (one plugin per format family)
   └──────────┬───────────────────┘
              ▼
   ┌──────────────────────────────┐
   │ Stage 3: ASSEMBLER PLUGINS   │   Merge multi-table DataFrames (relational join, vertical stack, index-align)
   └──────────┬───────────────────┘
              ▼
   ┌──────────────────────────────┐
   │ Stage 4: HARVESTER PLUGINS   │   Convert dense signals/snapshots → summary feature rows (optional)
   └──────────┬───────────────────┘
              ▼
   ┌──────────────────────────────┐
   │ Stage 5: NORMALIZER PLUGINS  │   Map output into canonical schema (timestamps, entity keys, column names)
   └──────────┬───────────────────┘
              ▼
        Canonical CSV → ML Pipeline Node 1
```

### How Existing Datasets Map to This Pipeline

| Dataset | Discovery | Parser | Assembler | Harvester | Normalizer |
|:---|:---|:---|:---|:---|:---|
| **NASA Li-ion Battery `.mat`** | ZIP/dir walker | `mat_parser` | Cycle flattener (struct → rows) | — | Timestamp + capacity normalizer |
| **C-MAPSS TXT (FD001–FD004)** | ZIP walker | `whitespace_txt_parser` | Train/Test/RUL joiner | — | Column renamer (s1–s21) |
| **SCADA Excel DPR Logs** | ZIP walker | `scada_excel_parser` | Vertical month stacker | — | Multi-level header flattener |
| **IMS / FEMTO Bearings** | Directory snapshot walker | `csv_parser` | — | Signal → statistical features | RUL target derivation |
| **Solar Generation** | ZIP walker | `csv_parser` | Multi-table join (generation + weather on `DATE_TIME`) | — | Entity key normalizer (`PLANT_ID`) |
| **Solar Parquet Inverters** | ZIP walker | `parquet_parser` | Inverter + weather join on `timestamp` | — | Metadata JSON enrichment |

---

## 4. Plugin Interface Specification

### 4.1 Deterministic Plugin Selection Model

Do **not** rely only on `can_handle()` rejection. A generic CSV plugin and a SCADA-specific CSV plugin can both correctly say "yes, I can parse this." Selection must be deterministic and reproducible.

**Selection cascade (highest precedence first):**

$$
\text{winner} = \operatorname{argmax}(\text{policy\_override},\ \text{priority},\ \text{confidence})
$$

But only consider plugins where `supported=True` and `confidence ≥ 0.70`:

| Step | Source | Rule |
|:---|:---|:---|
| 1 | **Dataset manifest / user config** | Explicit plugin name override — use that plugin, validate compatibility |
| 2 | **Plugin priority** | Declared in plugin metadata (higher wins) |
| 3 | **Specificity + confidence** | Returned by `probe()` logic — schema/layout pattern matching |
| 4 | **Fail closed** | If tie persists → mark as ambiguous, produce report, trigger agent |

**Resolution examples:**

| Situation | Result |
|:---|:---|
| Dataset manifest explicitly names a plugin | Use that plugin; validate compatibility |
| SCADA plugin detects timestamp/tag/value at 0.96 confidence | Use SCADA plugin |
| Generic CSV scores 0.99, SCADA is 0.30 | Use generic CSV (SCADA below threshold) |
| Two domain plugins both score 0.90+ | **Ambiguous** — require explicit rule or human selection |
| No plugin passes 0.70 threshold | Produce unsupported-layout report → trigger agent |

> [!CAUTION]
> Silent misclassification is **much more dangerous** than a compilation failure. Always fail closed on ambiguity rather than randomly selecting a parser.

### 4.2 Core Interfaces

```python
@dataclass
class MatchResult:
    """Returned by every plugin's probe() method."""
    supported: bool
    confidence: float          # 0.0 to 1.0
    reasons: list[str]         # Human-readable explanation of match/rejection
    detected_family: str | None


class BasePlugin(ABC):
    """Common interface for all compiler plugins."""
    plugin_id: str             # Stable identifier (never changes across versions)
    plugin_name: str           # Human-readable name
    version: str               # Semantic version (e.g. "1.2.0")
    contract_version: int      # Plugin API contract version (separate from impl version)
    stage: str                 # "discovery" | "parser" | "assembler" | "harvester" | "normalizer"
    priority: int              # Higher wins after policy override (e.g. 80 for SCADA, 10 for generic)

    @abstractmethod
    def probe(self, context: PipelineContext) -> MatchResult:
        """Non-destructive inspection: can this plugin handle the current context?"""

    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """Process the context and return updated context."""
```

### 4.3 Stage-Specific Interfaces

| Stage | Key Methods | Input | Output |
|:---|:---|:---|:---|
| **Discovery** | `probe()` + `discover(target_path)` | Raw archive/dir path | `FileInventory` + layout classification |
| **Parser** | `probe()` + `parse(filepath)` | Single file path | `Dict[str, DataFrame]` keyed by logical table |
| **Assembler** | `probe()` + `assemble(tables)` | Multiple parsed tables | Merged/stacked logical datasets |
| **Harvester** | `probe()` + `harvest(tables)` | Raw signal DataFrames | Summary feature DataFrames |
| **Normalizer** | `probe()` + `normalize(df)` | Any DataFrame | Canonical-schema DataFrame |

### 4.4 Plugin Metadata (YAML Declaration)

Each plugin declares its capabilities in metadata:

```yaml
# scada_excel_parser metadata
plugin_id: scada_csv_bundle
version: 1.2.0
contract_version: 1
priority: 80
handles:
  extensions: [".csv"]
  layout: "directory_or_zip"
  expected_columns_any: ["timestamp", "tag", "value"]
  expected_columns_all: ["timestamp"]
```

```yaml
# generic_csv_parser metadata
plugin_id: generic_csv
version: 1.0.0
contract_version: 1
priority: 10
handles:
  extensions: [".csv"]
```

So a SCADA CSV selects `scada_csv_bundle` (priority 80, confidence 0.96); an ordinary CSV falls back to `generic_csv` (priority 10, confidence 0.99).

---

## 5. Plugin Versioning & Reproducibility

### 5.1 Versioning Policy

Support **multiple installed versions** for development, testing, rollback, and reproduction — but enforce **one resolved active version per `plugin_id` in each compiler run**.

Do **not** create separate permanent IDs like `csv_parser_v1` and `csv_parser_v2`. Use stable plugin ID + semantic version:

```text
plugin_id: matlab_struct_parser
version: 1.4.2
contract_version: 1
```

**Semantic version rules:**

| Level | When to Bump | Example |
|:---|:---|:---|
| **Patch** (x.y.Z) | Bug fix, no expected output-contract change | 1.4.1 → 1.4.2 |
| **Minor** (x.Y.0) | New supported layout, optional capability, backward-compatible output | 1.4.2 → 1.5.0 |
| **Major** (X.0.0) | Changed canonical semantics, changed required fields, incompatible behavior | 1.5.0 → 2.0.0 |
| **Contract version** | Plugin API interface change (separate from impl) — controlled deprecation | contract_version: 1 → 2 |

### 5.2 Compilation Lockfile

Every compilation run produces a lockfile in the output manifest:

```yaml
# compiler_lock.yaml — written into output directory
compiler_version: 0.9.0
run_timestamp: "2026-07-24T08:40:00Z"
plugin_lock:
  zip_directory_discovery: "1.1.0"
  csv_parser: "1.0.0"
  scada_excel_parser: "1.2.0"
  matlab_struct_parser: "1.4.2"
  relational_join_assembler: "1.0.3"
  canonical_schema_normalizer: "2.0.0"
```

> [!IMPORTANT]
> The same raw ZIP must be reproducible later with the exact parser versions that created the CSV. The lockfile is the **single source of truth** for which plugin versions were active during a run.

### 5.3 Production Versioning Rules

- Resolve a single approved version in the registry per `plugin_id`.
- Pin it in the dataset manifest or compilation lockfile.
- Allow rollback to the prior approved version.
- **Never silently replace a plugin version during a run.**

---

## 6. Registry Discovery & Lifecycle

### 6.1 Startup-Only Discovery (Production)

A compiler run must have an **immutable plugin snapshot**. If plugins hot-reload halfway through processing a nested archive, two files in the same dataset could be compiled with different code versions. That breaks reproducibility, debugging, and auditability.

**Compiler lifecycle:**

```
1. Compiler starts
2. Registry discovers approved plugins from plugins/ directory
3. Registry validates plugin contracts and resolves version lock
4. The run receives an immutable PluginSnapshot
5. Every file in that run uses that snapshot
6. The compiler writes the snapshot into the output manifest (lockfile)
```

> [!CAUTION]
> Hot reload has real lifecycle risks: plugins may be invoked before fully initializing, leak resources on unload, or cause runtime version conflicts. **Hot reload is development-only, never mid-compilation.**

### 6.2 PluginRegistry Implementation

```python
class PluginRegistry:
    """Central registry for all compiler plugins."""

    def auto_discover(self, plugins_dir: Path) -> None:
        """Walk plugins/ directory, import all modules, collect @register_plugin classes."""

    def register(self, plugin: BasePlugin) -> None:
        """Register a plugin instance. Enforces one active version per plugin_id."""

    def get_plugins(self, stage: str) -> List[BasePlugin]:
        """Return all registered plugins for a given stage, sorted by priority desc."""

    def resolve(self, stage: str, context: PipelineContext,
                policy_override: Optional[str] = None) -> BasePlugin:
        """Deterministic selection: policy → priority → confidence → fail closed."""

    def snapshot(self) -> PluginSnapshot:
        """Return an immutable snapshot of all resolved plugin versions for this run."""
```

### 6.3 PluginSnapshot & Lockfile

```python
@dataclass(frozen=True)
class PluginSnapshot:
    """Immutable record of all plugin versions active in a compiler run."""
    compiler_version: str
    run_timestamp: str
    resolved_plugins: Dict[str, ResolvedPlugin]  # plugin_id → (version, contract_version, path)

    def to_lockfile(self) -> dict:
        """Serialize to YAML-compatible dict for output manifest."""
```

---

## 7. Scout Agent as Plugin Releaser

The agent does **not** hot-patch a live compiler. It follows a **build → test → approve → rerun** cycle:

```
1. Unknown dataset arrives
2. Compiler produces an unsupported-format or ambiguous-routing report
3. Agent identifies the missing stage (e.g. "PARSER_MISSING for .parquet")
4. Agent generates a new plugin file implementing BaseParserPlugin
5. Docker sandbox runs plugin contract tests + dataset fixture tests
6. On PASS → Agent promotes the new plugin version to plugins/ directory
7. A NEW compiler run starts with the new immutable PluginSnapshot
```

```
                                    ┌─────────────────────┐
                                    │ Unknown Dataset      │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │ Compiler Run #1      │
                                    │ (immutable snapshot) │
                                    │                      │
                                    │ RESULT: UNSUPPORTED  │
                                    │ gap: PARSER_MISSING  │
                                    │ format: .parquet     │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │ Scout Agent (LLM)    │
                                    │ Generates:           │
                                    │ parquet_parser.py    │
                                    │ v1.0.0, priority=50  │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │ Docker Sandbox       │
                                    │ --network none       │
                                    │ --memory 256m        │
                                    │                      │
                                    │ Contract test: PASS  │
                                    │ Fixture test:  PASS  │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │ Plugin PROMOTED      │
                                    │ → plugins/parsers/   │
                                    │   parquet_parser.py  │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │ Compiler Run #2      │
                                    │ (NEW snapshot with   │
                                    │  parquet_parser      │
                                    │  v1.0.0 resolved)    │
                                    │                      │
                                    │ RESULT: SUCCESS      │
                                    └─────────────────────┘
```

This keeps the agent **out of a live compiler process** and makes every behavior change traceable to a reviewed plugin release.

---

## 8. Proposed Directory Structure

```
aiconnex_zip_compiler/
├── __init__.py
├── compiler.py                    # [MODIFY] Thin pipeline executor — queries PluginRegistry
├── schema_gate.py                 # [KEEP]   Pre-compilation entry gate (unchanged)
├── scout.py                       # [MODIFY] Gap classifier targets plugin stages, follows release cycle
├── patch_proposer.py              # [MODIFY] LLM prompt generates BasePlugin subclasses
├── sandbox_runner.py              # [KEEP]   Docker-only sandbox (unchanged)
├── reporter.py                    # [MODIFY] Gap IDs include target_stage + target_plugin_interface
├── handoff.py                     # [KEEP]   ML pipeline handoff export (unchanged)
│
├── plugins/
│   ├── __init__.py                # [NEW] Auto-discovery loader (startup-only)
│   ├── base.py                    # [NEW] ABCs: BasePlugin, MatchResult, stage-specific interfaces
│   ├── registry.py                # [NEW] PluginRegistry with deterministic resolve()
│   ├── context.py                 # [NEW] PipelineContext + PluginSnapshot + lockfile
│   │
│   ├── discovery/
│   │   ├── __init__.py
│   │   └── zip_directory_discovery.py    # [REFACTOR from discovery.py]
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── csv_parser.py                 # [REFACTOR from discovery.py safe_read_csv] priority=10
│   │   ├── scada_excel_parser.py         # [REFACTOR from excel_converter.py] priority=80
│   │   ├── hdf5_parser.py               # [REFACTOR from hdf5_converter.py] priority=70
│   │   ├── mat_parser.py                 # [REFACTOR from mat_converter.py] priority=70
│   │   └── parquet_parser.py             # [REFACTOR from custom_converters/] priority=50
│   │
│   ├── assemblers/
│   │   ├── __init__.py
│   │   ├── relational_join_assembler.py  # [REFACTOR from relational_joiner.py]
│   │   └── vertical_stack_assembler.py   # [NEW]
│   │
│   ├── harvesters/
│   │   ├── __init__.py
│   │   └── signal_summary_harvester.py   # [REFACTOR from snapshot_aggregator.py]
│   │
│   └── normalizers/
│       ├── __init__.py
│       └── canonical_schema_normalizer.py # [REFACTOR from schema_mapper.py]
│
├── tests/
│   └── test_compiler_regression_suite.py  # [MODIFY] Test via PluginRegistry
│
└── Dockerfile.sandbox                      # [KEEP] Pre-built sandbox image
```

---

## 9. File-by-File Refactoring Map

### Phase 1: Plugin Infrastructure (Foundation)

| File | Action | Description |
|:---|:---|:---|
| `plugins/__init__.py` | **[NEW]** | Startup-only auto-discovery: scans all subdirs, imports `@register_plugin` classes |
| `plugins/base.py` | **[NEW]** | `BasePlugin`, `MatchResult`, `BaseDiscoveryPlugin`, `BaseParserPlugin`, `BaseAssemblerPlugin`, `BaseFeatureHarvesterPlugin`, `BaseSchemaNormalizerPlugin` |
| `plugins/registry.py` | **[NEW]** | `PluginRegistry` with deterministic `resolve()` (policy → priority → confidence → fail closed) |
| `plugins/context.py` | **[NEW]** | `PipelineContext`, `PluginSnapshot`, `CompileLockfile` |

### Phase 2: Extract Built-in Plugins from Monolith

| Old Monolith File | New Plugin File | Stage | Priority |
|:---|:---|:---|:---|
| `discovery.py` (312 lines) | `plugins/discovery/zip_directory_discovery.py` | Discovery | — |
| `snapshot_aggregator.py` (lines 19–25) | `plugins/discovery/snapshot_folder_discovery.py` | Discovery | — |
| `discovery.py` → `safe_read_csv()` | `plugins/parsers/csv_parser.py` | Parser | 10 |
| `excel_converter.py` (200 lines) | `plugins/parsers/scada_excel_parser.py` | Parser | 80 |
| `hdf5_converter.py` (100 lines) | `plugins/parsers/hdf5_parser.py` | Parser | 70 |
| `mat_converter.py` (100 lines) | `plugins/parsers/mat_parser.py` | Parser | 70 |
| `custom_converters/solar_parquet_converter.py` | `plugins/parsers/parquet_parser.py` | Parser | 50 |
| `relational_joiner.py` (200 lines) | `plugins/assemblers/relational_join_assembler.py` | Assembler | — |
| (new) | `plugins/assemblers/vertical_stack_assembler.py` | Assembler | — |
| `snapshot_aggregator.py` (lines 28–173) | `plugins/harvesters/signal_summary_harvester.py` | Harvester | — |
| `schema_mapper.py` (100 lines) | `plugins/normalizers/canonical_schema_normalizer.py` | Normalizer | — |

### Phase 3: Rewire Core Modules

| File | Action | Description |
|:---|:---|:---|
| `compiler.py` | **[MODIFY]** | Replace direct imports with `registry.resolve()` at each stage. Write lockfile on completion. |
| `scout.py` | **[MODIFY]** | Gap classifier emits stage-targeted IDs. Agent follows build → test → approve → rerun cycle. |
| `patch_proposer.py` | **[MODIFY]** | LLM system prompt generates `BaseParserPlugin` subclasses with `probe()` + `parse()` + metadata |
| `reporter.py` | **[MODIFY]** | Gap IDs enriched with `target_stage`, `target_plugin_interface`, `contract_version` |

### Phase 4: Delete Old Monolith Files

| File | Action |
|:---|:---|
| `discovery.py` | **[DELETE]** |
| `excel_converter.py` | **[DELETE]** |
| `hdf5_converter.py` | **[DELETE]** |
| `mat_converter.py` | **[DELETE]** |
| `relational_joiner.py` | **[DELETE]** |
| `schema_mapper.py` | **[DELETE]** |
| `snapshot_aggregator.py` | **[DELETE]** |
| `custom_converters/` | **[DELETE]** |

---

## 10. Pros, Cons & Key Risks

### ✅ Pros

| Benefit | Detail |
|:---|:---|
| **Minimal blast radius** | Agent adds ONE plugin file — never touches `compiler.py` or other plugins |
| **Deterministic selection** | Policy override → priority → confidence → fail closed. No random routing. |
| **Reproducible outputs** | Lockfile pins exact plugin versions. Same ZIP + same lockfile = same CSV, always. |
| **Independent testability** | Each plugin gets its own fixture set, unit test, and Docker sandbox validation |
| **Scalable extensibility** | New formats = new plugin, not new core branch |
| **Safe agent model** | Agent is a plugin releaser, never a live code mutator. Build → test → approve → rerun. |
| **Parallel development** | Multiple developers/agents can add plugins simultaneously without merge conflicts |
| **Rollback** | Revert one plugin version without affecting any other stage |
| **Auditability** | Every compilation manifest records exactly which plugin versions produced the output |
| **Simpler LLM prompts** | LLM generates one ABC subclass with `probe()` + `parse()`, not a full converter function |

### ⚠️ Cons

| Drawback | Mitigation |
|:---|:---|
| **Migration effort** | ~15–20 files to create/refactor — mitigated by strangler-fig (old + new coexist during transition) |
| **Indirection overhead** | Registry lookup + `probe()` calls add ~1–2ms per stage — negligible vs. I/O-bound parsing |
| **Learning curve** | Contributors must understand plugin interface — mitigated by clear ABCs, metadata YAML, and examples |
| **Debugging across stages** | Stack traces span plugin boundaries — mitigated by `PipelineContext` carrying full audit trail |
| **Over-abstraction for trivial datasets** | Single flat CSV runs through 5 stages — mitigated by short-circuit: if parser returns single clean table, skip assembler/harvester |
| **Lockfile maintenance** | One more file to manage — mitigated by automatic generation during `compiler.compile()` |

### 🔴 Key Risks

| Risk | Severity | Mitigation |
|:---|:---|:---|
| **Regression during migration** | **HIGH** | Strangler-fig: old code runs in parallel until replacement plugin passes identical fixtures. 8/8 tests green at every commit. |
| **Plugin ordering conflicts** | **HIGH** | Deterministic cascade: policy override → priority → confidence → fail closed. Never randomly select. Ambiguous matches produce explicit error reports. |
| **Silent misclassification** | **HIGH** | Minimum confidence threshold (0.70). Below threshold = unsupported. Ambiguous (two plugins >0.90) = fail closed + report. |
| **LLM generates invalid plugin** | **MEDIUM** | Docker sandbox validates syntax + contract compliance + functional execution before promotion. Invalid plugins are BLOCKED. |
| **Version drift across runs** | **MEDIUM** | Lockfile written into every output manifest. Same lockfile = same behavior, always. |
| **Mid-run plugin mutation** | **MEDIUM** | `PluginSnapshot` is frozen at startup. Registry is read-only after `snapshot()` is called. |
| **Circular imports** | **LOW** | Strict rule: plugins import ONLY from `plugins.base` and `plugins.context`. Never import `compiler.py` or `scout.py`. |
| **Performance regression** | **LOW** | Plugin dispatch adds <2ms per stage. Real bottleneck is I/O. Benchmark before/after on Dataset-TAS.zip. Target: ≤5% overhead. |
| **Contract version mismatch** | **LOW** | Registry validates `contract_version` at discovery time. Incompatible plugins are rejected at startup, not at runtime. |

---

## 11. Design Decisions (Resolved)

| Question | Decision | Rationale |
|:---|:---|:---|
| Two plugins claim a file | **Policy override → priority → confidence/specificity → fail closed on tie** | Deterministic, reproducible, no silent misclassification |
| Plugin versions | **Multiple versions stored; exactly one resolved active version per `plugin_id` per run** | Supports rollback and reproduction without runtime ambiguity |
| Naming | **Stable `plugin_id` + semantic version**, not separate `*_v1` / `*_v2` IDs | Clean identity model |
| Registry discovery | **Once at startup for production** | Immutable snapshot per run guarantees reproducibility |
| Hot reload | **Development-only, never mid-compilation** | Prevents version drift within a single dataset run |
| Agent changes | **New plugin version in sandboxed branch → test → approve → register → rerun** | Agent is a releaser, not a live patcher |
| Reproducibility | **Write `compiler_lock.yaml` into every output manifest** | Same ZIP + same lockfile = identical CSV output |

---

## 12. Verification Plan

### Automated Tests

```bash
# Full regression (must stay 8/8 green throughout migration)
python -m pytest tests/test_compiler_regression_suite.py -v

# New plugin-specific tests
python -m pytest tests/test_plugin_registry.py -v
python -m pytest tests/test_parser_plugins.py -v
python -m pytest tests/test_assembler_plugins.py -v

# Plugin contract validation
python -m pytest tests/test_plugin_contracts.py -v

# End-to-end Scout Agent loop with Docker sandbox
python scratch/test_schema_assessment.py
```

### Manual Verification

- Run `python aic/run_pipeline.py --dataset data/raw/Dataset-TAS.zip --output workspace_data/test_run` to confirm canonical handoff to ML pipeline Node 1
- Verify `compiler_lock.yaml` is written into output directory with correct resolved versions
- Verify `workspace_data/compiler_evolution_log.json` records plugin-level gap classifications

### Benchmark

- Compare compilation time of `Dataset-TAS.zip` before and after migration
- Target: ≤5% overhead from plugin dispatch

---

## 13. Migration Execution Order

> [!TIP]
> **Strangler-fig pattern**: new plugins coexist with old monolith code. Old code is deleted only after its replacement plugin passes all tests.

| Step | Phase | Files Touched | Gate |
|:---|:---|:---|:---|
| 1 | Infrastructure | `plugins/base.py`, `registry.py`, `context.py`, `__init__.py` | Unit test: registry can register, resolve, snapshot |
| 2 | CSV Parser Plugin | `plugins/parsers/csv_parser.py` | Passes `test_relational_solar_dataset_compilation` |
| 3 | SCADA Excel Parser | `plugins/parsers/scada_excel_parser.py` | Passes `test_excel_multi_sheet_extractor` |
| 4 | HDF5 + MAT Parsers | `plugins/parsers/hdf5_parser.py`, `mat_parser.py` | Passes existing HDF5/MAT test fixtures |
| 5 | Relational Assembler | `plugins/assemblers/relational_join_assembler.py` | Passes `test_relational_solar_dataset_compilation` |
| 6 | Normalizer Plugin | `plugins/normalizers/canonical_schema_normalizer.py` | Passes schema mapping tests |
| 7 | Discovery Plugin | `plugins/discovery/zip_directory_discovery.py` | Passes full discovery integration test |
| 8 | Signal Harvester | `plugins/harvesters/signal_summary_harvester.py` | Passes snapshot aggregation test |
| 9 | Rewire `compiler.py` | Uses `PluginRegistry.resolve()` + writes lockfile | Full 8/8 regression green |
| 10 | Rewire `scout.py` + `patch_proposer.py` | Stage-targeted gaps + plugin-class LLM prompts | Docker sandbox loop passes |
| 11 | Delete old monolith | Remove `discovery.py`, `excel_converter.py`, etc. | Full 8/8 regression still green |
| 12 | New plugins | `parquet_parser.py`, `vertical_stack_assembler.py` | New test fixtures pass |
