# AI-ConneX Frontend — Complete Audit & Architecture Doc

> Location: `x:\TAS\AICONNEX\frontend`
> Stack: React 19 · TypeScript · Vite 6 · Tailwind CSS v4 · Express · Google Gemini
> Purpose: Visual control plane for the "Total Automation Solutions (TAS)" MLOps / AutoML platform.

---

## 1. What this folder is

`frontend/` is a **React 19 + TypeScript single-page application (SPA)** for **AI-ConneX**, the TAS MLOps / AutoML orchestration platform. It is the visual front-end for:

- A **9-microservice ML pipeline backend** (ports `:8000`–`:8008`): profiler, DAG matcher/orchestrator, prepare, feature synth, validation gates, trainer, serving/monitor.
- **Jane**, a conversational AI assistant (Google Gemini via `@google/genai`, with a LangGraph backend).

It is served by a small **Express + Vite middleware server** (`server.ts`) that also exposes two local API routes (`/api/health`, `/api/predict`).

There is **no react-router** — navigation is a **state machine** inside `App.tsx` driven by a `ViewMode` union type.

Origin: scaffolded from a **Google AI Studio** app template.

---

## 2. Tech stack

| Concern | Choice |
|---|---|
| UI framework | React 19 (`react`, `react-dom`) |
| Language | TypeScript ~5.8 |
| Bundler / dev server | Vite 6 (`@vitejs/plugin-react`) |
| Styling | Tailwind CSS v4 (`@tailwindcss/vite`) + CSS design tokens |
| Server | Express 4 (dev: Vite middleware; prod: static `dist/`) |
| AI | `@google/genai` (Gemini) + Jane/LangGraph backend |
| Charts | `plotly.js` / `react-plotly.js`, `recharts`, `@kanaries/graphic-walker` |
| Icons | Material Symbols (font) + `lucide-react` |
| Animation | `motion`, custom canvas, CSS keyframes |

---

## 3. Top-level file tree

```
frontend/
├── index.html               # HTML entry — mounts #root, imports /src/main.tsx
├── package.json             # deps + scripts (dev/build/start/lint)
├── vite.config.ts           # Vite: react+tailwind plugins, @ alias, HMR toggle
├── server.ts                # Express server (:3002) — /api/health, /api/predict (Gemini)
├── tsconfig.json            # TS config (ES2022, react-jsx, @/* alias, noEmit)
├── metadata.json            # AI Studio app metadata
├── README.md                # AI Studio run-locally instructions
├── .env.example             # env template
├── .gitignore
├── public/                  # static assets
│   ├── tas-logo.png
│   ├── connex-logo.png
│   ├── connexx-dark.png
│   ├── connexx-white.png
│   └── cover-bg.jpg
├── src/                     # THE APPLICATION (see section 4)
├── dist/                    # build output (generated)
├── .vite/                   # vite cache (generated)
├── node_modules/            # deps (generated)
├── desktop_ui/              # SEPARATE standalone Node app (hero + chatbot server)
└── keynote_presentation/    # SEPARATE standalone keynote/animation suite (ports 3000/3001)
```

### Top-level files explained

| File | Role |
|---|---|
| `index.html` | Loads fonts (Hanken Grotesk, Inter, JetBrains Mono, Material Symbols), mounts `<div id="root">`, imports `/src/main.tsx`. Title: `AI_CONNEX \| Total Automation Solutions`. |
| `package.json` | Name `react-example`. Scripts: `dev` (`tsx server.ts`), `build` (Vite build + esbuild server bundle → `dist/server.cjs`), `start` (`node dist/server.cjs`), `lint` (`tsc --noEmit`). |
| `vite.config.ts` | React + Tailwind plugins; `@` → project root; pre-bundles graphic-walker & styled-components; HMR disabled when `DISABLE_HMR=true`. |
| `server.ts` | Express on port `3002`. Initializes Gemini client. `/api/health` → status JSON. `/api/predict` → sends telemetry JSON to `gemini-3.6-flash` for nominal/warning/critical verdict, with heuristic fallback (temp/vibration thresholds). Dev = Vite middleware, prod = serve `dist/`. |
| `tsconfig.json` | ES2022, `react-jsx`, bundler resolution, `@/*` path alias, `noEmit`. |
| `metadata.json` | `{ name: "AI-Connexx", ... MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API }`. |

### Auxiliary standalone sub-apps (NOT part of the React build)

- **`desktop_ui/`** — `stitch-aiconnex-enterprise` Node/Express app: hero landing page + AI chatbot server with intent logging. Sub-folders: `chat_app/`, `desktop_app/`, `industrial_automl_app/`, `user-intents/`, plus `server.js`.
- **`keynote_presentation/`** — "Project Genesis" cinematic keynote + animation suite. Plain HTML/JS/CSS. Hero dashboard on `:3000`, keynote animation on `:3001`. Files: `genesis.html/js/css`, `app.js`, `canvas-motion.js`, `audio-synth.js`, `server.js`, `server-genesis.js`, sub-folders `hero_desktop_3000/`, `keynote_animation_3001/`.

These live alongside the SPA but are **never imported** by it.

---

## 4. `src/` application structure

```
src/
├── main.tsx                 # React entry — mounts <ThemeProvider><App/></ThemeProvider>
├── App.tsx                  # CENTRAL HUB — state router, domain state, backend orchestration
├── index.css                # global Tailwind + CSS design tokens + animations
├── types.ts                 # ViewMode + all domain interfaces
├── context/
│   └── ThemeContext.tsx     # theme provider (currently light-locked)
├── data/
│   └── initialData.ts       # seed/mock data (models, env vars, runs, notifications, DAGs, recipes)
├── components/              # reusable chrome & widgets (12 files)
└── views/                   # the screens (19 files + DataExplorer/ with 5 sub-views)
```

### Boot chain
```
index.html → /src/main.tsx → <ThemeProvider> → <App/>
```

- **`main.tsx`** — creates React root, wraps `<App/>` in `<StrictMode>` + `<ThemeProvider>`, imports `index.css`.
- **`index.css`** — global styles + tokens (`--bg-page`, `--text-primary`, `glass-panel`, `btn-primary`, `fadeIn`/`scaleIn` animations).
- **`context/ThemeContext.tsx`** — provider **hard-locked to light mode** (`toggleTheme` is a no-op); `useTheme()` → `{ isDark: false }`.
- **`types.ts`** — central types. `ViewMode` = union of every routable view id. Also `SidebarStyle`, `ModelRegistryItem`, `EnvironmentVariable`, `BillableRun`, `DAGNode`, `AsyncJobStep`, `AsyncJobProgress`, `SystemNotification`.
- **`data/initialData.ts`** — `INITIAL_MODELS`, `INITIAL_ENV_VARS`, `INITIAL_BILLABLE_RUNS`, `INITIAL_NOTIFICATIONS`, `DAG_FAMILY_NODES` (10 ML families), `RECIPE_STEPS_NODES` (17 recipe steps incl. VG_1/VG_2).

---

## 5. `App.tsx` — the central hub

`App` is the single source of truth and the router. There is no URL routing; `currentView: ViewMode` decides which view renders in `<main>`.

**Responsibilities:**

1. **Navigation** — `navigateTo(view)` sets `pendingView` + `isTransitioning` → shows `<PageTransition>` → on complete, `currentView = pendingView`. Also listens to global `window` events: `aic-navigate`, `aic-open-jane`, `aic-toast`.
2. **Domain state** — `models`, `envVars`, `billableRuns`, `notifications`, plus pipeline context: `compiledCsvPath`, `activeRunId`, `activeDagId`, `activeFamily`, `executionMode`.
3. **Real backend orchestration**:
   - `handleRunDagPipeline` → `:8000/api/v1/profile` → `:8001/api/v1/pipeline/run` → polls `:8001/.../status`, streaming logs into `AsyncLoadingModal`.
   - `handleRunSequentialPipelines` → FIFO queue of datasets; `runSinglePipelineExecution` is the per-dataset runner.
4. **Simulated jobs** — `startDescriptiveJob` drives fake multi-step progress for register-model / export-report / adjust-quotas / add-env-var.
5. **Inference** — `handleRunInference` → local `/api/predict`.
6. **Jane integration** — wires `ChatBotModal` (session id, narration, LangGraph interrupts, `/api/jane/seed` bridge that pre-fills the compiler wizard).

**Always-on chrome** (rendered on every screen): `<Sidebar>`, `<Header>`, `<Footer>`, floating "Talk to Jane" button, `<ChatBotModal>`, `<NotificationDrawer>`, `<AsyncLoadingModal>`, and conditionally `<PageTransition>`.

---

## 6. `src/components/` — reusable pieces

| Component | What it shows / does | Connects via |
|---|---|---|
| **Sidebar.tsx** | Switcher: slim vs orbital based on `sidebarStyle`. | renders Slim/Orbit sidebar |
| **SlimFloatingSidebar.tsx** | Default left icon-dock. Groups: *Core Workflow Studio* (Hero, Upload, Data Explorer, Model Explorer, Deployment, Agents, ML Studio) + *Admin & Master Data* (Master, Admin, Templates, Quotas, Workspace, Logs, Settings, Support). Portal tooltips. | `onSelectView` → `navigateTo` |
| **OrbitArcSidebar.tsx** | "OrbitalARC": mouse-following, pinnable **semi-circular radial menu**; outer arc (core views) + inner arc (quick nodes); magnetic hover physics; right-click page list. | `onSelectView` |
| **Header.tsx** | Fixed top bar: TAS logo (→ hero), dynamic view title, **"9 Services Online"** health popover (all 9 ports/latency), **Actions** quick-menu, "Talk to Jane", notification bell w/ unread badge. | `onRunQuickTask`, `onOpenChatBot`, `onToggleNotifications`, `onSelectView` |
| **Footer.tsx** | Fixed bottom status bar: platform operational, copyright, Privacy/Terms/SOC2 links. | reads `sidebarStyle` |
| **TasLogo.tsx** | TAS logo pill + "AI-ConneX" wordmark. | used in Header/Compiler |
| **ConnexxBrand.tsx** | Inline Connexx wordmark image (dark/white). | branding spots |
| **PageTransition.tsx** | Full-screen navigation overlay: spinning ring, destination label, per-destination fake step list, progress bar. | App `isTransitioning`, `onComplete` |
| **ChatBotModal.tsx** | **Jane assistant** drawer (docked/centered). Own markdown→HTML renderer (code/tables/headings), quick-prompt & option chips. Calls `:8000`→`:5000`→relative `/api/v1/jane/chat` and streaming `/api/agent/chat`. Handles LangGraph interrupts, session creation, execution-mode, `OPEN_UPLOAD_CONTROLLER`/`NAVIGATE_VIEW`. | deep App wiring |
| **NotificationDrawer.tsx** | Right drawer listing `SystemNotification`s (read/unread), "mark all read". | `notifications`, `onMarkAllRead` |
| **AsyncLoadingModal.tsx** | "CASCADE RUNNING" modal: overall %, per-stage step cards, live log console, background/cancel. | App `activeJob` (`AsyncJobProgress`) |
| **InteractiveDotGrid.tsx** | Decorative canvas: animated red/blue dot grid w/ mouse-proximity liquid physics. | standalone |

---

## 7. `src/views/` — the screens

Each view is conditionally rendered by `App.tsx` from `currentView`.

| View file | ViewMode | What it renders |
|---|---|---|
| **HeroLandingView** | `hero` | Landing page. Top nav + CTAs into Compiler, Agent Fleet, Templates, Quotas. App entry point. |
| **CompilerView** | `compiler` | Multi-table dataset upload/ingestion wizard. Own `FIFOQueue`/`QueueNode` classes for sequential runs. Drives Jane narration/interrupts; triggers profiling; hands compiled CSV to Data Explorer. |
| **DataExplorerView** | `data_explorer` | Dataset/telemetry explorer. Tab container mounting 5 sub-views (pipeline stages). "Approve deliverables" → `:8000/api/v1/train_models` → navigate to Model Explorer. |
| **ModelExplorerView** | `model_explorer` | Trained-model ledger. Tabs: ledger / charts / industrial-explain. Per-model metrics (accuracy, MAE, RMSE, latency, memory, match score); deploy actions. |
| **DeploymentStudioView** | `deployment` | Deploy + inference playground. Prepared-dataset vs trained-model; test via custom JSON / uploaded dataset / agent tester; math-layer select (minmax/fft/zscore…). |
| **AgentManagerView** | `agent_manager` | Agent fleet orchestrator: agent configs (endpoint, provider, temperature, ports, RAG docs, replicas) + API telemetry call log. |
| **OrchestratorBoardView** | `orchestrator_board` | Visual node board: draggable pipeline nodes (Ingestion→Orchestration→Engineering→Execution→Deployment) with connections; each maps to a `viewId` and navigates on click. |
| **PipelineStudioView** | `pipeline_studio` | ML monitoring + inference. JSON payload editor → `/api/predict`; register-model modal; model list. |
| **WorkflowView** | `workflow` | DAG recipe orchestrator diagram. Pick family (`DAG_FAMILY_NODES`), view recipe steps (`RECIPE_STEPS_NODES`) incl. VG_1/VG_2. Tabs: diagram / recipe specs / logs. Triggers `onRunDagPipeline`. |
| **DagInspectorView** | `dag_inspector` | Browser for the 1,993 Master DAG registry — searchable DAG cards (family, topology, matching rules, stages); select DAG to run. |
| **MasterDataView** | `master_data` | Recipe/master-data manager by category (preparing/feature-eng/splitting/training/evaluating), each mapped to a backend service folder + port. |
| **TemplatesView** | `templates` | Template library: VG checklists, family configs, process boilerplates (editable JSON defaults). |
| **WorkspaceView** | `workspace` | File workspace browser — directory tree + file preview (tabular/json/text); select compiled CSV → Data Explorer. |
| **QuotasView** | `quotas` | GPU/compute quotas & billing — billable runs table (paginated, tier filter), export report, adjust quotas. |
| **AdministrationView** | `administration` | Env-var / secrets manager — list, mask/unmask, add-variable modal. |
| **DeveloperStudioView** | `developer_studio` | Live stdout log stream — simulated INFO/WARN/ERROR/DEBUG telemetry; filter/search/streaming toggle. |
| **SettingsView** | `settings` | Platform settings — cluster region, batch size, autoscale, and **sidebar style switch** (slim ↔ orbital). |
| **SupportView** | `support` | Docs & support hub — architecture specs + priority support cards. |
| **PipelineNodeView** | `vg1` / `vg2` | Generic validation-gate node screen (node 7 = VG1, node 8 = VG2). Checks service health; uploads; shows API results across raw/prepared/engineered paths. |

### `views/DataExplorer/` — tabs inside DataExplorerView (pipeline stages)

| Sub-view | Stage | Renders |
|---|---|---|
| **PrePrepare.tsx** | Pre-cleaning | Profiling with rich Plotly charts. |
| **PostPrepare.tsx** | After preparation | Before/after SVG comparison charts (imputation, outliers, scaling). |
| **PostFE.tsx** | After feature engineering | Branch-flow SVG visualizations (purple accent). |
| **PostTrain.tsx** | After split/train/evaluate | Split-strategy donut + metric charts (pink accent). |
| **AdHocExplorer.tsx** | Free exploration | Lazy-loaded **Graphic Walker** (Tableau-style drag-drop builder) in an error boundary. |

---

## 8. Navigation graph

```
                                 ┌─────────────┐
                                 │  HeroLanding │  (hero)  ← app entry
                                 └──────┬───────┘
             ┌──────────────┬──────────┼───────────┬──────────────┐
             ▼              ▼           ▼           ▼              ▼
        Compiler      AgentManager  Templates    Quotas      (Talk to Jane)
        (compiler)   (agent_manager)(templates)  (quotas)     ChatBotModal
             │
   upload + Jane narrate
             │  :8000 profile → :8001 run → poll status  (AsyncLoadingModal)
             ▼
      DataExplorer ──tabs──► PrePrepare · PostPrepare · PostFE · PostTrain · AdHoc
      (data_explorer)
             │  approve deliverables → :8000 train_models
             ▼
      ModelExplorer ──────► DeploymentStudio ──────► PipelineStudio (inference)
      (model_explorer)       (deployment)             (pipeline_studio)

  Sidebar / Header / OrchestratorBoard can jump to ANY view directly:
    workflow · dag_inspector · master_data · workspace · administration ·
    developer_studio · settings · support · vg1 · vg2 · orchestrator_board
```

**Navigation mechanism (no react-router):**
```
click (Sidebar / Header / Board / Jane)
  → navigateTo(view)
  → PageTransition overlay plays (per-destination fake steps)
  → handleTransitionComplete() → currentView = pendingView
  → <main> renders the matching view
```
Any component can also navigate by dispatching the `window` event `aic-navigate`.

---

## 9. The core MLOps journey (happy path)

```
Hero
  → Compiler (upload)                          [Jane narrates via ChatBotModal]
  → :8000 /api/v1/profile
  → :8001 /api/v1/pipeline/run
  → poll :8001 /api/v1/pipeline/{id}/status    (AsyncLoadingModal streams logs)
  → Data Explorer  (PrePrepare→PostPrepare→PostFE→PostTrain / AdHoc)
  → approve → :8000 /api/v1/train_models
  → Model Explorer
  → Deployment Studio (inference)
```

### Jane ↔ App bridge
```
ChatBotModal creates session → App stores janeSessionId
Jane returns OPEN_UPLOAD_CONTROLLER
  → App seeds /api/jane/seed
  → pre-fills Compiler inputs (target, problem type, domain…)
  → docks Jane, navigates to `compiler`
Jane NAVIGATE_VIEW action → navigateTo(target_view)
SSE narration / interrupts → flow back into the modal
```

### Async jobs
```
long action → AsyncJobProgress → AsyncLoadingModal
  (real polling for pipelines · simulated steps for admin actions)
  → completion pushes SystemNotification → NotificationDrawer
```

---

## 10. Data & state ownership

- **`App.tsx`** owns all domain state (`models`, `envVars`, `billableRuns`, `notifications`, pipeline context) and passes it as props; views call back via `on*` handlers.
- **`initialData.ts`** seeds it · **`types.ts`** types it · **`ThemeContext`** provides the (light-locked) theme.
- Cross-component messaging without prop-drilling uses `window` custom events: `aic-navigate`, `aic-open-jane`, `aic-toast`.

---

## 11. Backends the frontend expects

| Target | Endpoints | Purpose |
|---|---|---|
| Local Express (`server.ts`, :3002) | `/api/health`, `/api/predict` | health + Gemini inference |
| Microservices `:8000`–`:8008` | `/api/v1/profile`, `/api/v1/pipeline/run`, `/api/v1/pipeline/{id}/status`, `/api/v1/train_models` | profiler, DAG matcher/orchestrator, prepare, feature synth, gates, trainer, serving/monitor |
| Jane / LangGraph | `/api/v1/jane/chat`, `/api/agent/chat` (SSE), `/api/jane/seed` | assistant chat, streaming, session seeding (`:8000`→`:5000` fallback) |

The 9 nodes (from Header health popover):

| Node | Service | Port |
|---|---|---|
| 1 | Dataset Profiler | 8000 |
| 2 | DAG Matcher | 8001 |
| 3 | Recipe Orchestrator | 8002 |
| 4 | Data Prepare | 8003 |
| 5 | Feature Synthesizer | 8004 |
| 6 | Validation Gate 1 | 8005 |
| 7 | HPO AutoML Trainer | 8006 |
| 8 | Validation Gate 2 | 8007 |
| 9 | Model Serving / Monitor | 8008 |

---

## 12. One-paragraph summary

The frontend is a single React SPA where **`App.tsx` is a state-machine router** that renders one of ~20 views inside persistent chrome (Sidebar + Header + Footer + Jane assistant + async/notification modals). Views map 1:1 onto the 9-node MLOps backend and are stitched together by `ViewMode` navigation, a shared `App`-level state store, `window`-event messaging, and the Jane assistant bridge. The `desktop_ui/` and `keynote_presentation/` folders are separate standalone demo/marketing apps bundled in the same directory but excluded from the React build.
