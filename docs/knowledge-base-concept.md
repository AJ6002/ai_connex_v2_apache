# AIConnex Knowledge Base — Conceptual Design Document

> Status: **Conceptual only.** No infrastructure, database, or code referenced in this document has been built yet. This is the record of what we decided to build and why, before building it.

---

## 1. What problem is this solving?

AIConnex agents (Pre-Upload, Scout, Workflow, Platform, HITL) currently make decisions using only what's in front of them at that moment — the current conversation, the current dataset, hardcoded prompt templates. There is no shared, persistent, structured place where:

- The system's own capabilities and rules live in one place
- Domain/industrial knowledge (what is RUL, what is SCADA, what is predictive maintenance) is available to any agent
- Terminology (synonyms, canonical terms) is resolved consistently
- What was learned about a dataset on a previous run is remembered
- ML methodology guidance (when to use ridge vs. lasso, how to evaluate time-series models) informs pipeline decisions

The Knowledge Base (KB) is the system that fixes this: a shared, versioned, traceable knowledge layer that every agent draws from and writes back to.

---

## 2. The starting point — the original diagram

The discussion began with a proposed architecture:

```
AI AGENTS → CONTEXT BUILDER → [DETERMINISTIC | STRUCTURED/SEMANTIC | RETRIEVAL/DOCUMENT] → KNOWLEDGE GRAPH → EVIDENCE PACK → LLM
```

**What was right about it:**
- Splitting knowledge into three access patterns (exact lookup / semantic relationships / document retrieval) is the correct mental model
- The Evidence Pack — a structured envelope that carries source, version, section/page, entity, and relevance alongside the actual content — is the right mechanism for traceability

**What was missing, identified through review:**
1. The Context Builder had no defined contract (what goes in, what comes out, who owns routing)
2. The Knowledge Graph's role was ambiguous ("selective" was undefined)
3. There was no write-back path — agents only ever read, never contributed what they learned back into the KB
4. There was no versioning/staleness model — nothing would tell you when a source was outdated
5. Document chunking/embedding strategy was unspecified

These five gaps became the basis for everything that followed.

---

## 3. The five knowledge domains (V1 scope)

Rather than one undifferentiated "knowledge base," the system's knowledge was split into five domains, each with different authorship, freshness, and access characteristics:

| Domain | What it contains | Who creates it | How it grows |
|---|---|---|---|
| **Platform Knowledge** | AIConnex's own rules, schemas, node capabilities, supported formats, registries | The team, from the existing codebase | Manual — updated when capabilities change |
| **Industrial Domain Knowledge** | Engineering concepts — RUL, SCADA, predictive maintenance, sensor semantics, unit ontologies | Public engineering literature + team domain expertise | Expanded per industry as new domains are onboarded |
| **Business / Industrial Terminology** | Synonym maps, canonical term definitions, column-name pattern libraries | Team-curated, informed by real datasets already seen | Grows every time a user says something the system doesn't recognize |
| **Dataset Knowledge** | Facts about specific datasets — papers, schemas, quirks, plus what Scout discovers on each upload | Dataset papers/docs (static) + Scout's own analysis output (dynamic) | Automatic — every Scout run adds to it |
| **ML Methodology Knowledge** | Algorithm properties, metric definitions, feature engineering guidance, evaluation methodology | Public ML literature + internal pipeline documentation | Mostly stable, occasional updates as pipeline evolves |

---

## 4. The key realization — two kinds of material, not five databases

Despite five knowledge domains, everything reduces to **two basic kinds of material**:

```
AIConnex Knowledge
│
├── A. EXACT / STRUCTURED INFORMATION
│      rules, definitions, schemas, capabilities, terminology
│      → deterministic lookup, no ambiguity
│
└── B. DOCUMENT INFORMATION
       manuals, papers, standards, dataset docs, methodology docs
       → requires semantic search, ambiguity is expected
```

This collapses the five domains into a simple mapping of "mechanism per domain," not five separate storage systems:

| Domain | Deterministic | Structured | Knowledge Graph | Document/RAG |
|---|---|---|---|---|
| Platform | **Primary** | Yes | Limited | Yes |
| Industrial Domain | Some | Yes | Yes | **Primary** |
| Terminology | **Primary** | **Primary** | Yes | Supporting |
| Dataset | Some | Yes | Yes | **Primary** |
| ML Methodology | Some | Yes | Yes | **Primary** |

**There are not five separate databases. There are five knowledge domains, each implemented using the appropriate mix of a small number of underlying mechanisms.**

---

## 5. The three underlying technologies

Every domain, regardless of which knowledge area it belongs to, is stored using one of three mechanisms:

| Mechanism | Handles | Why |
|---|---|---|
| **YAML / JSON files** | Deterministic, exact-lookup knowledge (rules, schemas, registries, synonym maps) | Zero infrastructure, version-controlled in git, human-editable, instant load |
| **PostgreSQL** | Structured relational knowledge, knowledge-graph entities/relationships, write-back records | Exact queries, JSONB for nested data, transactional integrity |
| **Qdrant (vector DB)** | Document/semantic search — chunked embeddings of papers, manuals, docs | Built for approximate-nearest-neighbor similarity search with metadata filtering |

No fourth technology is needed for V1.

---

## 6. Where the raw material actually comes from

A critical clarification made during this discussion: **most of the raw material already exists.**

- Platform Knowledge → already in the codebase (schemas, registries, node definitions)
- Industrial Domain → public engineering literature (freely available standards, glossaries) + team expertise
- Terminology → already implicit in datasets already processed (HTDS, C-MAPSS) — just needs to be written down
- Dataset Knowledge → dataset papers (public, one-time collection) + Scout's own output (automatic, ongoing)
- ML Methodology → public ML literature (scikit-learn docs, papers) + internal pipeline docs

The work is not *finding* the knowledge. The work is **collecting it under a disciplined process, verifying it, and structuring it so it's traceable and searchable.**

---

## 7. The critical correction — treat this as a library, not a folder of PDFs

The most important shift in this discussion was reframing the entire effort:

> You are building a library for AIConnex. Every item that enters gets **classified, verified, labelled, versioned, and made searchable** — not simply dumped into a folder and thrown at an embedding model.

This means the build sequence must NOT start with infrastructure (databases, vector stores) or with bulk content collection. It must start with **governance of what is allowed to enter the KB at all.**

### The governing question

Rather than asking:
> "What PDFs do I need?"

The right question is:
> "What knowledge does an AIConnex agent need, and what is the authoritative source for it?"

---

## 8. The Source Register — the control point

Before any document, registry, or fact enters the KB, it must be registered in a master inventory: the **AIConnex Knowledge Source Register**.

Every candidate piece of knowledge gets a row with:

| Field | Purpose |
|---|---|
| `knowledge_id` | Unique identifier (e.g. `KB-DATASET-001`) |
| `knowledge_area` | Which of the 5 domains it belongs to |
| `title` | What it is |
| `source_type` | Standard / Official Documentation / Research Paper / Government / Internal |
| `source_organization` | Who published it |
| `source_url` | Where it came from |
| `domain` | Industry tag |
| `authority` | A = primary/official, B = secondary/reputable, C = internal/team-authored |
| `tenant_scope` | Global or tenant-specific |
| `version` | Source version |
| `license` | Usage rights |
| `status` | Pending → Approved / Rejected |
| `document_location` | Where the raw file will live once approved |
| `ingestion_status` | Pending → Parsed → Normalized → Chunked → Embedded |
| `review_status` | Pending → Reviewed |

**The rule: nothing is ingested, chunked, or embedded until it has a row with `status = Approved`.** No exceptions — not even internal team documents.

---

## 9. The full conceptual pipeline (end to end)

Once the governance discipline is in place, knowledge moves through a fixed sequence:

```
1.  Define the knowledge model         (2 kinds of material, 5 domains — done in this discussion)
2.  Build the Source Register          (the control point — nothing skips this)
3.  Collect sources                    (Platform / Terminology / Industrial / Dataset / Methodology)
4.  Review and approve each source     (authority check, license check, relevance check)
5.  Parse and normalize documents      (preserve headings, tables, page numbers, citations)
6.  Attach metadata, version, provenance (every document gets an identity)
7.  Store the original document        (S3/MinIO — never only in the vector DB)
8.  Create structured catalogue entries (PostgreSQL — the "library catalogue": where is it, who owns it, what version)
9.  Chunk document content              (by document structure — chapter/section/subsection — not arbitrary character counts)
10. Create embeddings                   (only now does the vector DB get involved)
11. Build the retrieval service         (agents never query the vector DB directly)
12. Assemble Evidence Packs             (source + version + section/page + entity + relevance, attached to every fact)
13. Build the Context Builder           (decides what knowledge a given agent/phase needs, fans out to the right stores)
14. Connect to agents                   (agents consume knowledge; they do not own or directly query the KB)
```

Two additional facts reinforce this ordering:

- **S3/MinIO holds the truth.** PostgreSQL is the catalogue (metadata, provenance, ownership). Qdrant is only a search index over approved, catalogued content — never the sole copy of anything.
- **Traceability is mandatory, not optional.** Every conclusion an agent reaches from retrieved knowledge must be traceable back through: Evidence → Chunk → Section/Page → Document → Version → Source. This is what makes the system auditable for an industrial platform, where "why did the agent say that?" must always be answerable.

---

## 10. What was corrected mid-discussion

An earlier draft of the "immediate next steps" jumped straight to creating YAML registries and standing up PostgreSQL/Qdrant before any registration or review process existed. This was identified as the same mistake the whole redesign was meant to prevent — infrastructure-first, governance-later, which reproduces "a random collection of files" problem just with YAML instead of PDFs.

**The corrected immediate sequence:**

1. Create the 9 empty folders only (`01_Source_Register` through `09_KB_Specifications`) — no content yet
2. Create exactly one file: the Source Register (spreadsheet/CSV)
3. Populate it first with **Platform Knowledge** only — because it requires no external sourcing decisions, it's already in the existing codebase
4. Review and approve those Platform rows — the first real checkpoint, proving the discipline works before anything harder
5. For each approved row, tag it as "exact/structured" or "document/explanatory" — still no infrastructure built

Only after this proves out on the easiest category does the plan move to Industrial Domain, Dataset, and Methodology sourcing — and only after *that* does anything touch PostgreSQL, Qdrant, or a document pipeline.

---

## 11. Physical folder structure (target — not yet built)

*(See **Section 14 — Final Target Schema Resolution** below for the locked authoritative 15-tier target tree).*

---

## 12. Open items deferred beyond V1

These were identified but explicitly not part of the current build scope:

- Write-back path implementation (agents contributing learned knowledge back into the KB) — conceptually designed, not yet sequenced into the immediate steps
- Multi-tenant scoping beyond the `tenant_scope` field in the register
- Caching / async fan-out / re-indexing performance work
- Full Knowledge Graph population beyond the entities strictly needed for V1 domains
- Automated staleness detection (content-hash based re-ingestion triggers)

---

## 13. Summary — what we are actually building

Not a chatbot memory store. Not a folder of PDFs fed to an embedding model.

**A governed, versioned, traceable knowledge library for AIConnex**, where:
- Every fact an agent uses can be traced to an approved, authoritative source
- Five knowledge domains map onto only three underlying technologies (YAML, PostgreSQL, Qdrant)
- Nothing enters the system without passing through a Source Register review
- Agents consume knowledge through a Context Builder and Evidence Pack contract — they never touch a store directly
- The system is designed to grow (new domains, new datasets via Scout write-back) without ever losing the ability to answer "why did the agent say that?"

---

## 14. Final Target Schema Resolution

### 4 Conflict Resolutions (Verbatim)

1. **`tenant` omitted**: No top-level `tenant` tier in the V1 target tree; tenant scoping is handled via metadata filtering (`tenant_scope` / `tenant_id` field in register, DB, and Qdrant).
2. **`embeddings=metadata-only`**: Vector storage lives inside Qdrant vector DB (`platform_kb_embeddings`), `10_embeddings` directory holds embedding model & manifest metadata only.
3. **`contracts=single-source-in-02_platform`**: Manifest & contract schemas live in `02_platform/contracts/` as single source of truth, not duplicated across directories.
4. **`structured=git-seed-loads-into-postgres`**: Seed JSON/YAML entities & relationship files live in git (`04_structured/`) and load into PostgreSQL on boot.

### Naming Decision
- `snake_case` is the target naming convention for directories (`aiconnex_knowledge/`).
- No rename of existing built folders on disk yet (`AIConnex-Knowledge/` remains active on disk until full migration).

### Authoritative Locked Target Tree (15-Tier, Tenant Removed)

```text
aiconnex_knowledge/
│
├── 00_governance/
│   ├── README.md
│   ├── knowledge_architecture.md
│   ├── knowledge_lifecycle.md
│   ├── source_authority_policy.md
│   ├── ingestion_policy.md
│   ├── retention_policy.md
│   ├── versioning_policy.md
│   ├── tenant_isolation_policy.md
│   └── access_control_policy.md
│
├── 01_source_register/
│   ├── source_register.csv
│   ├── source_register.json
│   ├── approved_sources.csv
│   ├── rejected_sources.csv
│   └── deprecated_sources.csv
│
├── 02_platform/
│   ├── architecture/
│   ├── agents/
│   ├── compiler/
│   ├── parsers/
│   ├── ml_platform/
│   ├── contracts/
│   ├── workflows/
│   ├── operations/
│   └── adr/
│
├── 03_deterministic/
│   ├── capabilities/
│   ├── registries/
│   ├── rules/
│   └── schemas/
│
├── 04_structured/
│   ├── entities/
│   ├── relationships/
│   └── metadata/
│
├── 05_terminology/
│   ├── canonical_terms.yaml
│   ├── synonyms.yaml
│   ├── abbreviations.yaml
│   ├── acronyms.yaml
│   ├── business_terms.yaml
│   └── platform_terms.yaml
│
├── 06_raw_documents/
│   └── platform/
│       ├── architecture/
│       ├── contracts/
│       ├── agents/
│       ├── compiler/
│       ├── ml_platform/
│       ├── operations/
│       └── adr/
│
├── 07_normalized_documents/
│   └── platform/
│       ├── architecture/
│       ├── contracts/
│       ├── agents/
│       ├── compiler/
│       ├── ml_platform/
│       ├── operations/
│       └── adr/
│
├── 08_document_metadata/
│   ├── document_registry.json
│   ├── document_versions.json
│   ├── document_sources.json
│   ├── document_authority.json
│   └── document_lineage.json
│
├── 09_chunks/
│   └── platform/
│       ├── architecture/
│       ├── contracts/
│       ├── agents/
│       ├── compiler/
│       ├── ml_platform/
│       ├── operations/
│       └── adr/
│
├── 10_embeddings/
│   ├── embedding_manifest.json
│   ├── embedding_model.json
│   └── platform/
│
├── 11_retrieval/
│   ├── retrieval_config.yaml
│   ├── retrieval_policies.yaml
│   ├── metadata_filters.yaml
│   ├── reranking_config.yaml
│   └── retrieval_test_cases.json
│
├── 12_evidence/
│   ├── evidence_schema.json
│   └── examples/
│
├── 13_provenance/
│   ├── ingestion_runs.jsonl
│   ├── document_events.jsonl
│   ├── chunk_events.jsonl
│   ├── embedding_events.jsonl
│   └── retrieval_events.jsonl
│
├── 14_validation/
│   ├── corpus_validation_report.json
│   ├── metadata_validation_report.json
│   ├── chunk_validation_report.json
│   ├── retrieval_evaluation_report.json
│   └── traceability_report.json
│
└── 15_manifests/
    ├── knowledge_base_manifest.json
    ├── platform_kb_manifest.json
    └── ingestion_manifest.json
```

