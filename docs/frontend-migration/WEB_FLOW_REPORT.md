# AI-ConneX `web/` — Flow Report

> What's built, every view/page, and how it's all connected.
> Reflects the actual state of `x:\TAS\AICONNEX\web` as of this report. Companion to `FRONTEND_MIGRATION_PLAN.md`.

---

## 1. What this is

`web/` is the new frontend, built contract-first per the migration plan (Sprints 0–4 complete). It is **not** the old `frontend-deprecated/` — it's a clean rebuild on:

```
Router (react-router 7)
  ↓
Feature views (features/*)
  ↓
Entity hooks (entities/*/hooks.ts)  ← TanStack Query, server state
  ↓
Entity API functions (entities/*/api.ts)
  ↓
API client (api/client.ts)  ← env-driven base URL, auth-injection point
  ↓
MSW mock layer (mocks/*)  ← currently serves ALL data (no live backend wired yet)
```

Everything visible right now runs against **mocked data** (`VITE_USE_MOCKS=true` in `.env`). No live FastAPI backend is connected yet.

---

## 2. Boot flow

```
index.html
  → src/main.tsx
      - reads config/env.ts (VITE_API_BASE, VITE_USE_MOCKS)
      - if mocks on: starts MSW worker (mocks/browser.ts → handlers.ts)
      - renders <App/>
  → app/App.tsx
      - wraps everything in <QueryClientProvider> (TanStack Query)
      - renders <RouterProvider router={router}/>
  → app/router.tsx
      - defines every route (see §4)
```

---

## 3. The two top-level surfaces

There are exactly **two visual "modes"** in the app, split at the router root:

| Surface | Route | Shell | Theme |
|---|---|---|---|
| **Public marketing page** | `/` | None — standalone `LandingPage` | Light, own scoped palette (`--lp-*`) |
| **Product application** | everything else | `AppShell` (sidebar + topbar + Jane dock + footer) | Light (app default, flipped from an earlier dark-first build via token override) |

The Landing page is intentionally isolated — it doesn't use the app's design tokens, doesn't show the sidebar, and its CTAs (`GET STARTED`, `BOOK A DEMO`) link into `/intake` to enter the product.

---

## 4. Every route, page by page

### 4.1 Landing (`/`)
**File:** `features/landing/components/LandingPage.tsx`
Public page: announcement banner → sticky nav → hero (dot-grid bg, headline + CTAs) → "Building blocks, not black boxes" platform showcase (interactive tab rail driving an Axon Agent Pipeline diagram) → dark transition section → footer. No backend calls — fully static/presentational.

### 4.2 Workspace
| Route | File | Shows |
|---|---|---|
| `/workspace` | `features/workspace/components/WorkspaceOverviewView.tsx` | Dashboard homepage: Quick Actions (→Intake/Data Studio/Deploy), Inference Throughput stat, Active Deployment stat, an "items requiring attention" banner when a job needs clarification, Active & Recent Jobs table (links into `/jobs/:id`), Recent Datasets panel |
| `/workspace/new` | `features/workspace/components/NewWorkspaceView.tsx` | Workspace creation form: name, region select, Private/Shared Cloud toggle → `useCreateWorkspace()` |

### 4.3 Intake (`/intake`)
**File:** `features/intake/components/IntakeView.tsx`
"Asset Registration" screen: `DROP_ZONE_ALPHA` drop card, `METADATA_CONFIG` panel (source select, sensitivity segmented control, owner ID), `RECENT_INTAKE` live list. **The only real "start a job" entry point:** clicking "Browse Local Files" calls `useInspectArchive()` → on success `useSubmitIntent()` → navigates to `/jobs/:jobId`.

### 4.4 Jobs
| Route | File | Shows |
|---|---|---|
| `/jobs/:jobId` | `features/jobs/components/JobView.tsx` (via `routes/jobs/JobRoute.tsx`) | Job detail — header (ID, status badge, title), 4 stat cards, **5 distinct states** driven by the mock job id: `job_running` (pipeline stepper + live streaming log console), `job_completed` (artifacts-ready card), `job_failed` (red failure banner + errored stage), `job_clarify` (interactive clarification banner — pick an answer, resolves live), `job_profiling`. Polls via `useJob(jobId)` (auto-refetches while status is live) |

### 4.5 Data Studio
| Route | File | Shows |
|---|---|---|
| `/data-studio` | `features/data-studio/components/DataStudioView.tsx` | Breadcrumb stage stepper (Discovery→Profile→Prepare→Features→Train→Evaluate), dataset header, resolved-tables sidebar, Machine-Ready score banner, 4 profile panels (Structural field table, Semantic PII/currency chips, Statistical histogram, Temporal density chart). The **Discovery** stage in the breadcrumb links onward |
| `/data-studio/discovery/:assetId` | `features/data-studio/components/DiscoverySegmentationView.tsx` | Discovery map (color-coded segment tiles with sample rows) + review cards (SEG_01/SEG_02) with working **APPROVE/REJECT** buttons via `useReviewDiscoverySegment()` — state mutates live |

### 4.6 Models
| Route | File | Shows |
|---|---|---|
| `/models` | `features/models/components/ModelsView.tsx` | Registry table (checkbox, ID→link, version, status pill, metrics, training run→links to job, deployment), empty-state handled, links to detail |
| `/models/:modelId` | `features/models/components/ModelDetailView.tsx` | Evaluation metrics (F1/latency/AUC-ROC with deltas + PR curve), Validation Results, Artifact Lineage stepper, Artifact References, Deployment History table |

### 4.7 Deployments
| Route | File | Shows |
|---|---|---|
| `/deployments` | `features/deployments/components/DeploymentsView.tsx` | Registry cards (status dot, model ref, latency/throughput/replicas, endpoint), empty-state handled, "Deploy New" |
| `/deployments/new` | `features/deployments/components/DeploymentConfigView.tsx` | Config form (model select, Production/Staging toggle, region, instance type, replicas) → `useCreateDeployment()` → back to registry |
| `/deployments/:deploymentId` | `features/deployments/components/DeploymentDetailView.tsx` | Identity & Config panel, Health & Performance (latency/throughput/error-rate + sparkline), Version History table with Rollback |

### 4.8 Agents (`/agents`)
**File:** `features/agents/components/AgentsView.tsx` — agent roster/status (least-detailed screen so far; not a dedicated Stitch design, built from the entity data available).

### 4.9 Admin — nested under one layout
**Layout:** `features/admin/components/AdminLayout.tsx` renders a 5-tab bar and an `<Outlet/>`; `/admin` redirects to `/admin/access-control`.

| Route | File | Shows |
|---|---|---|
| `/admin/access-control` | `features/admin/components/AdminView.tsx` | Active Personnel table, RBAC Metrics (seat usage), API Credentials cards |
| `/admin/audit-logs` | `features/admin/components/AuditLogsView.tsx` | Filterable immutable event table, FAILURE rows highlighted, pagination |
| `/admin/usage-quotas` | `features/admin/components/UsageQuotasView.tsx` | Billing cycle bar, Compute (GPU) radial ring, Storage tier bars |
| `/admin/workspace` | `features/admin/components/WorkspaceConfigView.tsx` | Workspace Identity, Tenant Config, Platform Policies (quarantine threshold, retention) |
| `/admin/system-states` | `features/admin/components/SystemStatesView.tsx` | Diagnostic gallery: validation failure, asset quarantined, 403, 503, empty-state — reference/QA screen, not a normal user path |

### 4.10 Component catalog (`/catalog`)
**File:** `routes/catalog/ComponentCatalog.tsx` — a live showcase of every design-system primitive (Button, Card, StatusBadge, Tabs, DataTable, Progress, Input, Dialog, Skeleton, EmptyState/ErrorState) rendered with real tokens. Developer/QA tool, not part of the product journey.

---

## 5. The persistent chrome (present on every product page)

`AppShell` (`app/shell/AppShell.tsx`) wraps every route except Landing:

- **Left sidebar** — brand ("AI-ConneX" / "Project Alpha" / "PRODUCTION ENVIRONMENT"), "NEW EXPERIMENT" button, domain-grouped nav: Workspace · Datasets(→Intake) · Data Studio · Jobs · Models · Deployments · Agents · Admin
- **Top bar** — search field, "Jane Agent" label, notification/account icons
- **Footer** — "System Status: API Operational" + version + Support link
- **Right-docked Jane panel** (`app/shell/JaneDock.tsx`) — see §7

---

## 6. How the pieces connect (data flow)

```
Feature view (e.g. IntakeView.tsx)
   │  calls a hook, never fetch() directly
   ▼
Entity hook (e.g. entities/job/hooks.ts → useSubmitIntent)
   │  wraps entity API function(s) in a TanStack Query mutation/query
   ▼
Entity API function (e.g. entities/job/api.ts → narrowIntent, submitParseJob)
   │  calls the one shared client
   ▼
apiClient (api/client.ts)
   │  builds request from config.apiBase (config/env.ts) — no hardcoded hosts anywhere
   ▼
MSW intercepts the request (mocks/handlers.ts)
   │  matches by capability path, returns fixture data (mocks/fixtures/*)
   ▼
Response flows back up → TanStack Query caches it → view re-renders
```

**Cross-page links that actually work today:**
```
Landing "GET STARTED"/"BOOK A DEMO"  →  /intake
Intake "Browse Local Files"          →  submits intent → /jobs/:jobId (new job)
Workspace "Recent Jobs" rows         →  /jobs/:jobId (existing mock jobs)
Workspace Quick Actions              →  /intake, /data-studio, /deployments/new
Data Studio "Discovery" breadcrumb   →  /data-studio/discovery/:assetId
Models registry rows                 →  /models/:modelId
Models "training run" link           →  /jobs/job_completed
Deployments registry cards           →  /deployments/:deploymentId
Deployments "Deploy New"             →  /deployments/new → back to /deployments
Admin tab bar                        →  /admin/{access-control,audit-logs,usage-quotas,workspace,system-states}
```

There is **no `window` event bus** and **no global mutable app state object** — every cross-component interaction goes through router navigation or a TanStack Query cache write.

---

## 7. Jane Assistant — current real state (important caveat)

The right-docked `JaneDock` is visible on every product page. What's real vs. cosmetic:

| Capability | Status |
|---|---|
| Live session transcript rendering | ✅ Real (mocked session data via `useJaneSession()`) |
| Click a clarification option (Staging/Production) | ✅ Real — calls `useResolveJaneClarification()`, mutates mock state |
| Execute a proposed action (`EXECUTE_JOB`) | ✅ Real — calls `useExecuteJaneAction()` |
| INTENT tab | ✅ Fully built |
| JOBS / ACTIONS tabs | ❌ **Stub** — renders "No {tab} to display" |
| **Free-text chat input** | ❌ **Not wired** — the input box has no state binding and `onSubmit` is a no-op; typing and sending currently does nothing |
| Real conversational backend (LangGraph/SSE) | ❌ Not connected — this is Phase 6 (`Task 6.1.3`) of the backend migration plan, and that plan currently targets the *old* deprecated frontend, not `web/` |

**Bottom line: you cannot yet have a real typed conversation with Jane.** The dock demonstrates a scripted clarification→action scenario only.

---

## 8. Design system (why it all looks consistent)

- **Tokens** (`styles/tokens.css`) — the only place color/spacing/type/radius values are declared, extracted from `STITCH-Design/*/code.html`.
- **Theme** (`styles/theme.css`) — overrides the raw tokens to light mode (the app default, per explicit instruction), without touching any component.
- **Primitives** (`components/ui/*`) — Button, Input, Card, Dialog, Tabs, DataTable, StatusBadge, Progress, EmptyState, ErrorState, Skeleton. Every feature view is built from these; none hardcode colors (enforced by an ESLint rule).

---

## 9. What's NOT yet done

- Free-text Jane chat + JOBS/ACTIONS dock tabs (see §7)
- The specific `ASSET_QUARANTINED` / PII-detection screen from Stitch (a generic version exists in System States, not the exact faithful one)
- Any live backend connection — everything currently runs on MSW mocks
- Frontend Phases 2–4 (scheduled ops, streaming/scale-out, distributed ML views) — explicitly gated until their backend phases exist, per the migration plan
