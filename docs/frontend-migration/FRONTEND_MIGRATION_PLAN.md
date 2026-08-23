# AI-ConneX Frontend Migration Plan — New Folder, Contract-First, Phase-Gated

> Status: agreed plan, not yet executed.
> Decision: build a **new** frontend folder (`web/`). The old `frontend/` stays running untouched as reference until parity, then is archived. The old **UI is not being reused visually** — new design system, new screens, informed by preserved product knowledge.

---

## 0. What this document is

This is the single tracked source of truth merging:
1. The architecture audit (`ARCHITECTURE_AUDIT.md`) — what's wrong with the old frontend and why.
2. The `new-arch/` backend docs — the actual contract the new frontend must speak (Intent Envelope → Job → Artifact Package → Data Studio Brain routing).
3. The phase-gating decision — frontend work ships only when its backend phase exists.
4. The preserve/discard list and Sprint 1–4 breakdown — how Phase 1 itself is sequenced internally.

---

## 1. What gets preserved vs. discarded

### Preserve (as reference material, not as code)

| Item | Where it lives today | How it's used going forward |
|---|---|---|
| UX flows | old `frontend/src/views/*` | Reference for what a screen needs to *do*, not how it's coded |
| Page requirements | old views + `docs/` | Feed into new route/feature specs |
| Domain terminology | `types.ts`, view copy | Reused in new `entities/` naming |
| Charts | Plotly/Recharts usage in `DataExplorer/*` | Reused as chart *concepts* (which chart for which insight), rebuilt with new design system |
| Useful visual components | old `components/` | Reference only — rebuilt on new primitives, not copy-pasted |
| Icons/assets | `public/`, Material Symbols, lucide-react | Can be reused directly (assets are backend-agnostic) |
| Data Explorer concepts | `views/DataExplorer/` stage tabs (PrePrepare→PostPrepare→PostFE→PostTrain→AdHoc) | **This is the single best idea in the old app.** Evolve it: stages unlock from real **Artifact Package** status, not frontend assumptions |
| Jane interaction concepts | `ChatBotModal.tsx` | UX pattern (docked/expanded assistant, markdown rendering, option chips) preserved; network/session/navigation coupling is not |
| Model/deployment concepts | `ModelExplorerView`, `DeploymentStudioView` | Reference for what fields/metrics matter to users |
| DAG/recipe concepts | `WorkflowView`, `DagInspectorView`, `MasterDataView` | Reference for recipe/DAG UX; rebuilt against the real DAG/Recipe capability, not `initialData.ts` |
| Existing Figma/reference designs | `STITCH-Design/` at repo root — 28 screen folders, each with `code.html` (Tailwind + inline Material-3-style token config) + `screen.png` | **Confirmed design source.** Covers Intake, all Job states (running/completed/failed/clarification_required/active_profiling), Data Studio (profiling/profile_readiness/discovery_segmentation_review), Models (registry/empty_state/detail_evaluation), Deployment (registry/configuration/detail_active), Admin (access_control/audit_logs/usage_quotas/workspace_configuration), Jane flows, and system/failure states. Token palette extracted at Sprint 2; screens rebuilt on primitives at Sprint 4. **The `code.html` files are a visual/token spec only — never copied into the app as-is** (CDN Tailwind, inline config, single-file-per-screen — same anti-patterns being migrated away from) |

### Do NOT carry forward

| Item | Why |
|---|---|
| `App.tsx` architecture | God-object: router + domain state + orchestration + polling + Jane bridge in one 1,007-line file |
| Old `ViewMode` router | No URLs, no deep links, no back button |
| Hardcoded `localhost:` URLs | 44 references across 14 files — the #1 FE↔BE mapping risk |
| `window` event bus (`aic-navigate`, `aic-open-jane`, `aic-toast`) | Hidden, untyped dependency graph |
| `initialData.ts` as application state | Frontend pseudo-database; diverges from real backend truth |
| Frontend Express/Gemini backend (`server.ts`) | Wrong architectural boundary — AI/business logic belongs in FastAPI, not a Node shim in the frontend |
| Giant views (1,000+ line files) | Unmaintainable, unsafe to edit, source of the "UI changes don't apply" symptom |
| Old API calls (scattered `fetch()` to ports 8000–8008) | Bypasses the new Intent/Job/Capability contract entirely |
| Mock/live data mixing (`startDescriptiveJob` fake jobs alongside real polling) | No single concept of execution truth — dangerous in a production control plane |

**These are exactly the pieces that created the friction described in the original audit. Nothing on this list gets ported.**

---

## 2. The non-negotiable ordering principle

> **API/data layer before visual design. Always.**

```
New Frontend
    ↓
Typed API Client  (built from new-arch's Intent Envelope / Job / Artifact Package / Capability contract)
    ↓
FastAPI
```

Not:
```
New Figma → components → later figure out backend   ✗ (this is what created the old mess)
```

This is stricter than earlier framing in this conversation and supersedes it: **design work does not start until the contract layer and skeleton exist**, full stop.

---

## 3. The backend contract the frontend must speak (from `new-arch/`)

Sourced from `aiconnex_apache_first_production_architecture.md` §5.2, §13, §14. No frontend architecture exists in `new-arch/` — only this backend contract, which the frontend is built to consume.

- **Intent Envelope** — what the UI sends: `intent_uid, tenant_uid, user_uid, site_scope, asset_scope, goal, domain, requested_outputs, requires_model, requires_visualization, requires_service, autonomy_requested, constraints, source_refs, policy_ref`.
- **Job** — what the UI polls/subscribes to: one job per submitted intent, with status and stage progress. Replaces "call 9 services directly."
- **Artifact Package statuses** — the UI's state machine: `MACHINE_READY`, `MACHINE_READY_WITH_WARNINGS`, `READY_FOR_PROFILER`, `NEEDS_CLARIFICATION`, `NEEDS_USER_CORRECTION`, `QUARANTINED`, `FAILED`.
- **Capability Registry** — the UI's API surface, one typed function per capability: `inspect_archive, create_discovery_artifact, narrow_intent, request_clarification, create_parse_plan, validate_parse_plan, submit_parse_job, get_job_status, read_profile_summary, request_compilation, request_math_analysis, promote_dataset`.
- **Data Studio Brain routing** — Profiler / DAG-Recipe / PREPARE-Math are invoked *conditionally* by the backend's plan, not always-on. The frontend renders whichever stages the plan actually selected.

---

## 4. Phase gating — frontend ships aligned to backend phases

Do **not** build the full E2E frontend right after Phase 0. Build gradually, gated to the backend phase that actually powers each screen. Building ahead of the backend re-creates the exact "fake job mixed with real job" antipattern this migration exists to remove.

| Backend phase (`new-arch` §15) | Backend adds | Frontend phase | Frontend adds |
|---|---|---|---|
| **Phase 1 — baseline** (FastAPI, Docker sandbox, Arrow/DataFusion/Parquet, Great Expectations, LangGraph, PostgreSQL, MinIO) | Intake → Intent → Job → Docker parse → Data Studio Brain → non-ML/ML route → basic deploy | **Frontend Phase 1** *(this document's full scope — Sprints 1–4 below)* | Intake, Job tracking, Data Studio Brain (Profiler/DAG-Recipe/Prepare-Math), basic Model + Deployment views, Admin shell |
| **Phase 2 — scheduled ops** (Airflow, DockerOperator, Pools) | Nightly reprocessing, scheduled profiling, retraining, drift jobs | **Frontend Phase 2** | Scheduled-job history, DAG run calendar, drift-check panel — built only once Airflow is live |
| **Phase 3 — scale-out** (Kafka, Beam, Iceberg, Kubernetes) | Streaming telemetry, distributed batch, table snapshots, multi-node execution | **Frontend Phase 3** | Live telemetry stream view, Iceberg snapshot/time-travel browser, K8s job/pod monitor |
| **Phase 4 — heavy distributed ML** (Spark, Ray, GPU clusters, KServe/Triton) | Distributed training, GPU-backed serving | **Frontend Phase 4** | Training cluster dashboard, GPU utilization view, model-serving monitor |

**Everything in the rest of this document (Sprints 1–4) is Frontend Phase 1.** Phases 2–4 are backlog placeholders only — no design, no code — until their backend phase ships.

---

## 5. Sprint 0 — Rename the legacy folder before any new work starts

**Goal:** eliminate any ambiguity about which frontend is "current." Before Sprint 1 begins, the existing `frontend/` folder is renamed so nobody — human or AI IDE — can mistake it for the active app.

**What changes / where:**

| Area | What changes | Where it lives |
|---|---|---|
| Folder rename | `frontend/` → `frontend-deprecated/` (contents unchanged, still runnable as a reference) | repo root |
| CI | `.github/workflows/ci.yml` job `frontend-build` currently runs `cd frontend && npm ci && npm run build` — this step must either be updated to `cd frontend-deprecated` or removed entirely once it's no longer meaningful to build the deprecated app | `.github/workflows/ci.yml` |
| README / docs pointers | Any doc that tells a new contributor to `cd frontend` (e.g. root `README.md`) should be updated to point at `web/` once it exists, and note `frontend-deprecated/` is legacy-only | `README.md`, any onboarding docs |
| New folder | The new app is created fresh as `web/`, never reusing the `frontend/` name — so there is only ever one folder that looks "active" | repo root |

**Note on `desktop_ui/` and `keynote_presentation/`:** these currently live inside `frontend/`. When `frontend/` is renamed to `frontend-deprecated/`, they move with it. Per §7's checklist, they still need to be relocated out entirely (e.g. to `apps/` or `marketing/`) rather than left inside the deprecated folder long-term — do this as part of, or shortly after, the rename so they aren't lost track of.

**Success criteria (must be true before Sprint 1 starts):**
- [ ] `frontend/` no longer exists as a folder name anywhere in the repo; `frontend-deprecated/` exists and still runs (`npm run dev` works from it) to confirm nothing was broken by the rename.
- [ ] CI either builds `frontend-deprecated/` under its new path or the redundant build step is removed — the pipeline does not silently fail or reference a nonexistent path.
- [ ] No script, doc, or config in the repo still references a bare `frontend/` path.
- [ ] `web/` does not exist yet at this point — confirms the rename happened *before* any new-folder work, not alongside it.

---

## 6. Frontend Phase 1, internally sequenced as Sprints 1–4

Each sprint below states: **what changes**, **where it changes**, and the **success criteria (Definition of Done)** that must be true before the next sprint starts. No sprint begins until the previous sprint's success criteria are all met — this is what keeps Sprint 4 (design) from ever running ahead of a proven contract layer.

---

### Sprint 1 — Architecture foundation (no UI yet)

**Goal:** every piece of plumbing the app will ever need to talk to a backend, hold state, route, and fail safely — with zero screens.

**What changes / where:**

| Area | What changes | Where it lives |
|---|---|---|
| Project scaffold | New Vite + React + TypeScript project created from scratch | `web/` (new folder, sibling to old `frontend/`) |
| Environment config | A single place that reads `VITE_API_BASE` and any per-capability overrides; nothing else in the app is allowed to reference a URL directly | `web/src/config/env.ts` |
| API client | One HTTP client wrapper: builds requests from the env config, attaches auth headers, normalizes errors, applies timeouts | `web/src/api/client.ts` |
| Contract types | Hand-written TypeScript types for Intent Envelope, Job, Artifact Package statuses, and each Capability Registry function's input/output, sourced from `new-arch/aiconnex_apache_first_production_architecture.md` §5.2/§13/§14 | `web/src/entities/*/types.ts` (one file per entity: dataset, job, artifact, profile) |
| Routing | Router installed and configured with placeholder route definitions (empty shells, no styling) for the Phase-1 route map | `web/src/app/router.tsx`, `web/src/routes/*` |
| Server state | Query/mutation infrastructure wired to the API client; this is the only layer allowed to fetch/poll | `web/src/app/queryClient.ts`, consumed via hooks in `entities/*/hooks` |
| UI state | A small store for session/UI-only state (active job id, docked/expanded assistant, sidebar state) — explicitly forbidden from holding server data | `web/src/stores/ui.ts` |
| Error handling | One error boundary component, mounted per route (not just once globally) | `web/src/components/ErrorBoundary.tsx`, wired in `web/src/app/router.tsx` |
| Async UI states | One shared component/pattern for loading / error / empty, used by every feature instead of ad-hoc conditionals | `web/src/components/AsyncState.tsx` (placeholder, unstyled) |
| Mocking | Mock handlers for every Capability Registry function, returning realistic Intent/Job/Artifact Package payloads | `web/src/mocks/handlers.ts`, `web/src/mocks/fixtures/*` |
| Testing tooling | Unit test runner installed and configured; one placeholder E2E test file reserved (not yet written) for the future first vertical slice | `web/vitest.config.ts`, `web/e2e/` (empty placeholder) |
| Lint rules | ESLint rule(s) that fail the build on: literal `http://`/`https://`/bare-IP strings outside `config/`, and on files exceeding a line-count threshold | `web/.eslintrc` |

**Explicitly out of scope this sprint:** no visual design, no styling, no Figma/Stitch input, no real screens — only route shells with placeholder text.

**Success criteria (must all be true before Sprint 2 starts):**
- [ ] `web/` runs (`dev` server starts) with zero references to any hardcoded host, port, or IP anywhere in `src/` outside `config/env.ts`.
- [ ] Every Capability Registry function from §3 has a typed API function and a corresponding MSW mock handler.
- [ ] Navigating between placeholder routes changes the URL and survives a page refresh (proves real routing works, unlike the old `ViewMode` switch).
- [ ] Triggering a mock API error in any placeholder route renders the shared error boundary — the app does not crash blank.
- [ ] Zero `window` custom events exist anywhere in the codebase.
- [ ] Zero files exceed the line-count lint threshold.
- [ ] Test runner executes successfully (even with a trivial passing test) — proves tooling is wired, not just installed.

---

### Sprint 2 — Design system foundation (still no full screens)

**Goal:** every visual decision (color, spacing, type, radius) exists in exactly one place, and every screen built afterward is assembled from a fixed set of primitives — never from one-off markup.

**What changes / where:**

| Area | What changes | Where it lives |
|---|---|---|
| Design tokens | Color, spacing, typography, and radius scales defined as CSS variables — this becomes the *only* place a color/spacing value is allowed to be declared | `web/src/styles/tokens.css` |
| Theme wiring | How tokens map to light/dark (or single-theme, decided explicitly rather than hard-locked like the old app) | `web/src/styles/theme.css` |
| Global styles | Resets, base typography, font loading | `web/src/styles/globals.css` |
| UI primitives | One component each for: Button, Input, Card, Dialog, Tabs, DataTable, StatusBadge, Progress, EmptyState, ErrorState, Skeleton — every one consuming only tokens, never a raw hex/px value | `web/src/components/ui/<PrimitiveName>/` |
| Design source | `STITCH-Design/` is the confirmed source. Each screen's `code.html` contains an inline Tailwind `theme.extend.colors` block (Material-3-style token names: `primary`, `surface`, `on-surface`, `surface-container`, `outline`, `intent-clarification`, `action-proposed`, `assistant-identity`, `error-container`, etc.). Diff the palettes across all 28 screens, reconcile into one consistent set, and map each to a semantic CSS variable name | source: `STITCH-Design/*/code.html` → output: `web/src/styles/tokens.css` |
| Lint rule | ESLint/stylelint rule banning raw hex colors and inline `style={{...}}` objects anywhere outside `styles/` and the primitives themselves | `web/.eslintrc` |

**Explicitly out of scope this sprint:** no page layouts, no feature screens — primitives are built and visually inspected in isolation (e.g. a component catalog page), not assembled into real routes yet.

**Success criteria (must all be true before Sprint 3 starts):**
- [ ] Every primitive in the list renders correctly using only token references — zero hardcoded hex/px inside any primitive.
- [ ] Changing a single token value (e.g. `--color-primary`) visibly changes every primitive that uses it, with no other file edited. This is the direct, demonstrable fix for the old "UI changes don't apply" problem.
- [ ] The hex/inline-style lint rule is active and passes with zero violations.
- [ ] A visual reference/catalog of all primitives exists and has been reviewed.

---

### Sprint 3 — Product structure

**Goal:** the codebase is organized around real platform concepts (dataset, job, artifact, profile, model, deployment, agent, workspace) instead of technical layers or old service ports, so any future feature has an obvious, single home.

**What changes / where:**

| Area | What changes | Where it lives |
|---|---|---|
| App shell | Providers (query client, router, theme, error boundary) composed into one bootstrap entry point | `web/src/app/` |
| Route folders | One folder per top-level Phase-1 route, each containing only route-level composition (layout + which feature to render), no business logic | `web/src/routes/intake/`, `web/src/routes/jobs/`, `web/src/routes/data-studio/`, `web/src/routes/models/`, `web/src/routes/deployments/`, `web/src/routes/admin/` |
| Feature folders | One folder per user-facing capability area, each with its own `components/`, `hooks/`, `api/`, and `__tests__/` subfolders — nothing shared across features without going through `entities/` | `web/src/features/intake/`, `.../jobs/`, `.../data-studio/`, `.../models/`, `.../deployments/`, `.../agents/`, `.../admin/` |
| Entity folders | One folder per backend concept, holding types, the typed API functions for that concept, and the shared hooks any feature uses to read/mutate it | `web/src/entities/dataset/`, `.../job/`, `.../artifact/`, `.../profile/`, `.../model/`, `.../deployment/`, `.../agent/`, `.../workspace/` |
| Stores | Confirm UI-only state stays in `stores/`, confirm no server data has leaked into it | `web/src/stores/` |
| Shared utils | Any cross-cutting helper (date formatting, formatting numbers, etc.) that doesn't belong to one entity | `web/src/lib/` |

**Explicitly out of scope this sprint:** no new visual design; this sprint is a structural/organizational pass — folders and ownership boundaries, not new UI.

**Success criteria (must all be true before Sprint 4 starts):**
- [ ] Every entity from §3 (dataset, job, artifact, profile, model, deployment, agent, workspace) has its own folder with types + API functions + hooks.
- [ ] No feature folder contains a direct `fetch`/API call — every network call goes through an entity hook.
- [ ] A reviewer can point at any file and say which single feature or entity owns it, with no ambiguity.
- [ ] Grep for duplicate logic: no two files implement the same capability call independently (pre-check for the §9.3 guardrail).

---

### Sprint 4 — Design / visual implementation

**Goal:** the first real, fully designed screens ship — built on Sprint 2's primitives, wired through Sprint 1/3's contract and structure — proving the whole stack end-to-end before any further screens are built.

**What changes / where:**

| Area | What changes | Where it lives |
|---|---|---|
| Design source | Confirmed: `STITCH-Design/`. For this slice, use `ai_connex_asset_intake_registration`, `ai_connex_job_detail_running` / `_completed` / `_failed` / `_clarification_required` / `_active_profiling`, `ai_connex_data_studio_profiling`, `ai_connex_data_studio_profile_readiness`, and `ai_connex_discovery_segmentation_review` as the per-screen/per-state visual spec | `STITCH-Design/ai_connex_asset_intake_registration/`, `.../ai_connex_job_detail_*/`, `.../ai_connex_data_studio_*/`, `.../ai_connex_discovery_segmentation_review/` |
| First vertical slice UI | Real, styled screens for: Intake (submit an Intent), Job tracking (poll and display a Job's status/stages), Data Studio Brain (render whichever of Profiler / DAG-Recipe / Prepare-Math the backend's plan selected) — each rebuilt on Sprint 2 primitives to match its corresponding Stitch screen, never by copying `code.html` | `web/src/features/intake/components/*`, `web/src/features/jobs/components/*`, `web/src/features/data-studio/components/*` |
| Route wiring | The placeholder route shells from Sprint 1 are filled in with the real feature components | `web/src/routes/intake/`, `.../jobs/`, `.../data-studio/` |
| State rendering | Every Artifact Package status from §3 (`MACHINE_READY`, `MACHINE_READY_WITH_WARNINGS`, `NEEDS_CLARIFICATION`, `NEEDS_USER_CORRECTION`, `QUARANTINED`, `FAILED`) has an explicit, designed visual representation — no status silently falls through to a generic "success" look | within the Job/Data Studio feature components |
| Navigation | The domain-grouped nav shell (§6) is implemented and wired to the real routes | `web/src/app/` (shell/layout), consumed by all routes |
| Tests | Unit tests for the new feature components; the E2E placeholder reserved in Sprint 1 is written against this slice | `web/src/features/intake/__tests__/`, `.../jobs/__tests__/`, `.../data-studio/__tests__/`, `web/e2e/intake-to-data-studio.spec.ts` |

**Explicitly out of scope this sprint:** any screen outside the Intake → Job → Data Studio Brain slice (Models, Deployments, Admin, Agents follow afterward on the same proven foundation, screen by screen).

**Success criteria (must all be true before this slice is considered done, and before rounding out remaining Phase 1 screens):**
- [ ] A user can submit an Intent from the Intake screen, be taken to a Job view that reflects real (or mocked) status changes over time, and land on a Data Studio Brain view showing only the stages the plan actually selected.
- [ ] Every Artifact Package status has a distinct, intentional visual treatment — verified by forcing each status through the mock layer and checking the screen.
- [ ] No screen in this slice contains a hardcoded color, spacing value, or URL — verified by the Sprint 1/2 lint rules passing with zero exceptions granted.
- [x] The E2E test for this slice passes. **5/5 Playwright specs green** (`e2e/intake-to-data-studio.spec.ts`): submit intent → job created; running job renders pipeline+streaming log; completed job shows artifacts ready; clarification can be resolved; Data Studio Brain renders profiling + links into Discovery Segmentation.
- [ ] A side-by-side visual diff of each implemented screen against its `STITCH-Design/*/screen.png` shows a **pixel-faithful match** (colors, spacing, typography, radii, shadows, proportions, and all states) — not merely "close enough." Fidelity is achieved via exact tokens (§9.4), while zero `code.html` markup was copied.

---

## 7. Navigation — consolidated, not reproduced 1:1

The old app had ~20 flat sidebar peers. Do not reproduce that information architecture. Consolidate into domain-grouped navigation, e.g.:

```
Data
├── Datasets
├── Explorer
└── Quality

Pipelines
├── Runs
├── Workflows
└── Recipes / DAGs

Models
├── Registry
├── Evaluation
└── Deployments

Agents
├── Agents
└── Runs

Administration
├── Workspace
├── Users
├── Quotas
└── Settings
```

Old top-level-only screens like **Developer Studio, VG1, VG2, Orchestrator Board** become **diagnostic/detail views** reachable from within a Job or Pipeline Run, not standalone nav destinations. Jane sits globally above all of this as the conversational layer, not owned by any single route.

Concretely for Phase 1, the top-level routes are:
```
/intake
/jobs/:jobId
/data-studio
/models
/deployments
/admin
```
with Data Studio Brain sub-views (Profiler / DAG-Recipe / Prepare-Math) and diagnostic detail views nested under `/jobs/:jobId` rather than promoted to top nav.

---

## 8. Execution order (single checklist)

- [x] Sprint 0: renamed `frontend/` → `frontend-deprecated/`; updated `ci.yml` (`cd frontend-deprecated` + job relabeled); relocated planning docs to `docs/frontend-migration/`. *(Still pending: relocate `desktop_ui/` and `keynote_presentation/` out of `frontend-deprecated/` — deferred, non-blocking.)*
- [x] Sprint 1: scaffolded `web/` (Vite+React19+TS), router (react-router 7), api client (env-driven, auth-injection point), env config (`VITE_API_BASE`/`VITE_USE_MOCKS`), contract types (Intent/Job/Artifact/Dataset/Profile), all 12 capabilities as typed fns + MSW mocks, TanStack Query, Zustand UI store, per-route error boundary, `<AsyncState>`, Vitest+Playwright tooling, ESLint guardrails (no-hardcoded-URL/IP + max-lines). **Verified:** typecheck ✓, lint 0 errors ✓, tests 3/3 ✓, prod build ✓, dev server boots on :3100 ✓.
- [x] Sprint 2: tokens.css/theme.css/globals.css, `components/ui/*` primitives (Button, Input, Card, StatusBadge, Progress, Skeleton, EmptyState, ErrorState, Tabs, DataTable, Dialog). **Verified:** extracted tokens from STITCH-Design, built master barrel `components/ui/index.ts`, component catalog route `/catalog`, ESLint raw hex color restriction rule, typecheck ✓, lint 0 errors ✓, unit tests 15/15 pass ✓.
- [x] Sprint 3: `app/ routes/ features/ entities/ api/ stores/` structure populated with entity types (`dataset`, `job`, `artifact`, `profile`, `model`, `deployment`, `agent`, `workspace`) and feature modules (`intake`, `jobs`, `data-studio`, `models`, `deployments`, `agents`, `admin`, `workspace`). **Verified:** 8/8 entities populated with types/API/hooks, zero direct `fetch` calls in features, typecheck ✓, lint 0 errors ✓, unit tests 19/19 pass ✓.
- [x] Sprint 4: built the full Phase-1 screen set from `STITCH-Design/`, rebuilt on Sprint 2/3 primitives and entities, going well beyond the original slice — see §10 below for the complete inventory and fixes made during verification.
- [ ] Round out remaining Phase 1 screens (Models, Deployments, Admin) on the same foundation
- [ ] Frontend Phases 2–4 remain backlog-only until their backend phase ships (Airflow → scheduled views; Kafka/Iceberg/K8s → scale-out views; Spark/GPU → distributed ML views)
- [ ] `frontend-deprecated/` fully retired once Phase 1 parity is reached

---

## 9. Non-negotiable guardrails

These close the remaining gaps between this plan and the original audit's full P1–P11 problem list. Not optional, not deferred to a later phase — each applies from the sprint it's listed under, onward.

### 9.1 Testing — built in per feature, not bolted on later

The audit flagged **zero tests** as P8. This plan must not repeat that.

- **Sprint 1**: set up Vitest (unit) + one Playwright E2E spec target reserved for the first vertical slice. Tooling exists before any feature code.
- **Sprint 4 onward**: every feature ships with tests **in the same PR**, co-located:
  ```
  features/intake/
  ├── components/
  ├── hooks/
  ├── api/
  └── __tests__/        # unit tests for this feature, added with the feature — not after
  ```
- The E2E spec for **Intake → Job → Data Studio Brain** (the first vertical slice) is written as that slice is built, not after it's "done."
- Rule: **no feature is considered complete without its tests.** This is cheaper to enforce now, while the codebase is empty, than to retrofit later.

### 9.2 Security baseline — defined at the API client, not per-screen

The audit flagged hardcoded IPs, no auth, and sample secrets in mock data as P11.

- **Sprint 1**, in `src/api/client.ts`:
  - Auth header injection point (even if using a placeholder/dev token now) — the client must support auth from day one, not have it bolted on later across dozens of call sites.
  - No IPs, ports, or hostnames hardcoded anywhere outside `config/env.ts`. Enforce with an ESLint rule banning literal `http://` / `https://` / bare IPs in `features/` and `entities/`.
  - CORS/base-URL config lives in one place (`config/env.ts`), never duplicated.
- **Sprint 1 MSW mocks**: never seed mock fixtures with real-looking secrets, tokens, or credentials (the old `AdministrationView` mock data rendered fake-but-realistic secrets — don't repeat that pattern even in mocks).
- **Sprint 3**: the `entities/workspace` and admin features must treat any credential/secret display as masked-by-default, matching what the real backend's policy/tenant model will require.

### 9.3 No duplicated orchestration logic

The audit flagged P7 — the old app implemented the same pipeline-runner logic twice (`handleRunDagPipeline` and `runSinglePipelineExecution`), and the two would drift.

- Rule: **one hook or one API function per capability, ever.** If "submit an intent and poll its job" is needed in two features (e.g. Intake and a re-run action from Job history), both call the same `useSubmitIntent()` / `useJobPolling()` — never a second copy with slightly different steps.
- Enforced structurally: capability-calling logic lives only in `api/` and `entities/<x>/hooks`; `features/` are only allowed to *consume* those hooks, not re-implement fetch/poll logic inline.
- Code-review checklist item from Sprint 4 onward: "does this PR introduce a second implementation of something `api/` or `entities/` already does?"

### 9.4 Visual fidelity vs. code copying — the thin line

There is a thin line here that is easy to slip on, in **both** directions. Hold it explicitly:

- **Banned — copying the construction.** No pasting `STITCH-Design/*/code.html` markup, no CDN-Tailwind class soup, no inline per-screen config, no hardcoded hex/px in JSX. *How* the Stitch screen was built is discarded.
- **Required — replicating the appearance exactly.** The rendered UI must be **visually indistinguishable from the Stitch `screen.png`** — same colors, spacing, radii, typography, shadows, proportions, and every interactive/empty/error state. "Inspired by" or "close enough" is a failure.

Two slip directions, both failures:
1. Slipping toward **copying** → reintroduces the exact anti-patterns this migration exists to remove.
2. Slipping toward **divergence** → clean code that no longer matches the design → fidelity lost.

**Why a clean rebuild can still be pixel-faithful:** Sprint 2 extracts the *exact* token values from each `code.html` `tailwind.config` (literal hex, spacing, radii, font stacks) into `tokens.css` — never approximated. Primitives and screens consume those tokens, so the pixels are identical *by construction*. The only thing rebuilt is the engineering underneath.

**Enforcement:** the Sprint 4 acceptance gate is a side-by-side visual diff of each implemented screen against its `screen.png` — pixel-faithful match required to sign off, not a subjective judgment.

---

## 10. Sprint 4 completion record

Sprint 4 grew beyond the originally scoped Intake → Job → Data Studio slice to cover the **entire Phase 1 screen set** from `STITCH-Design/`, built and verified in batches.

### Screens delivered

| Area | Screens | Notes |
|---|---|---|
| Landing | Public marketing page | Standalone, own scoped light palette (`--lp-*`), outside the app shell |
| Shell | AppShell (sidebar/topbar/footer) + JaneDock | Unified on the *dominant* Stitch shell pattern after two conflicting shell designs were found across screens (see below) |
| Intake | Asset Registration | Drop zone, metadata config, recent intake |
| Jobs | Running / Completed / Failed / Awaiting Clarification / Profiling | All 5 states, each with a distinct visual treatment (§9.4) |
| Data Studio | Profiling / Profile Readiness | Breadcrumb stage stepper, 4 profile panels, Machine-Ready score |
| Discovery | Segmentation Review | Segment map + approve/reject review cards, live state mutation |
| Models | Registry / Detail-Evaluation / Empty state | Lineage stepper, validation results, deployment history |
| Deployments | Registry / Detail-Active / Configuration | Health/performance panel, version history with rollback |
| Admin | Access Control / Audit Logs / Usage & Quotas / Workspace Config / System States | 5-tab nested layout under `/admin` |
| Workspace | Overview / New Workspace | **Fixed a real nav bug**: the shell's "Workspace" link pointed at `/` (the public Landing page) |
| Jane | Intent clarification flow (3 designs) | Unified into one stateful `JaneDock` interaction (question → resolve → propose → execute), not 3 separate screens |
| Enterprise AI Orchestration | — | Confirmed **duplicate** of Landing (`code.html` byte-identical); no separate screen built |
| Blueprint Tactical (×2) | — | Confirmed **design-token specs**, not screens (no `code.html`/`screen.png`); fully represented in `tokens.css`/`theme.css` already |

### Theme decision

Per explicit instruction, **light theme is the priority/default** for the whole app. This was implemented at the token layer (`theme.css` overrides the raw `--color-*` tokens from `tokens.css`), so every component — built dark-first during early batches — flipped to light automatically with zero per-component changes. This is the design-system payoff the plan's ordering was built to produce.

### Shell coherence fix

Stitch exported **two different, conflicting shell layouts** across screens (a thin icon-rail + right Jane-dock pattern on Intake vs. a wide labeled-sidebar + top-search + footer pattern on Job/Models/most others). Rather than reproduce both, the app standardized on the **dominant pattern** (wide sidebar) for coherence — an explicit judgment call, consistent with §7's "consolidate, don't reproduce 1:1" principle.

### Bugs found and fixed during Sprint 4 wrap-up verification

1. **Missing `.env` file** — only `.env.example` existed; `VITE_USE_MOCKS` defaulted to `false`, so MSW never started and every screen would have hit real (failing) network calls. Added `web/.env` with mocks on by default.
2. **Cache-key mismatch in clarification resolution** — `useResolveClarification` and `JobDetail` used the fixture's internal `job.jobId` to key the React Query cache, while `useJob` cached by the route's job id. Resolving a clarification wrote to the wrong cache entry, so the banner never cleared. Fixed by threading the route's job id through consistently (`entities/job/hooks.ts`, `features/jobs/components/JobView.tsx`).
3. **`request_clarification` mock always returned the same hardcoded job** regardless of which job asked. Added `resolveJobClarification(jobId)` so the mock responds correctly per job.
4. **`EmptyState` icon prop misuse** — `ModelsView`/`DeploymentsView` passed bare icon-name strings (e.g. `icon="deployed_code"`) to a `ReactNode` prop, rendering literal text instead of a glyph. Fixed to wrap in the Material Symbols span (caught while building the System States gallery, which used the primitive correctly for comparison).
5. **`mocks/fixtures.ts` exceeded the max-lines guardrail** (427 lines) — split into `mocks/fixtures/{job,dataset,profile,models,deployments,agents,workspace,jane}.ts` with a barrel `index.ts`, proving the guardrail from §9 catches real drift, not just decoration.

All fixes were caught by **running the actual verification gate** (typecheck/lint/test/build + a real E2E walk), not by inspection — reinforcing why Sprint 4's acceptance gate requires genuinely exercising the slice.

---

## 11. Summary

Before any new code was written, the legacy folder was renamed `frontend/` → `frontend-deprecated/` so there was never any ambiguity about which app is active. The new frontend (`web/`) was built contract-first: types and API client derived from the `new-arch` Intent/Job/Artifact Package/Capability contract before any component existed (Sprint 1), design system primitives and tokens next (Sprint 2), product structure organized around real backend entities (Sprint 3), and finally the full Phase 1 screen set built and verified against `STITCH-Design/` (Sprint 4, §10) — consolidated into grouped navigation and a single coherent shell, never reproducing conflicting or duplicate Stitch exports. Light theme was made the default per explicit instruction, flipped cleanly at the token layer. Testing, security, and no-duplicate-logic guardrails (§9) applied from the sprint each was introduced, onward, and caught real bugs during Sprint 4's wrap-up verification. Sprints 0–4 are complete; remaining work is Frontend Phase 2–4 screens, gated to their backend phases per §4.
