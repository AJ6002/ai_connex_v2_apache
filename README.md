# AIConnex — Autonomous Industrial AI & Multi-Agent Engineering Platform

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Node.js Version](https://img.shields.io/badge/node-18%2B%20%7C%2020%2B-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-compose%20ready-2496ED.svg)](https://www.docker.com/)
[![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite%20%2B%20TS-61DAFB.svg)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**AIConnex** is an enterprise multi-agent industrial AI platform designed for mission-critical industrial manufacturing, predictive maintenance (PdM), prognostics & health management (PHM), SCADA automation, and digital twins. 

The platform combines a **22-Node LangGraph Agentic Brain**, a **6-Layer Deterministic Knowledge Base (S1–S6)**, an **Autonomous 9-Node ML Assembly Line**, a **Universal Multi-Table Dataset Compiler**, and the **Jane Industrial AI Assistant**.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 AIConnex Full Platform                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘

                   ┌────────────────────────────────────────────────┐
                   │    Frontend: React + Vite + TypeScript         │
                   │    • Hero Landing  • Data Studio Compiler      │
                   │    • ML Studio     • Agent Fleet Orchestrator  │
                   └───────────────────────┬────────────────────────┘
                                           │ (Port 3001)
                                           ▼
                   ┌────────────────────────────────────────────────┐
                   │   Jane AI Gateway & LangGraph Microservices    │
                   │   • Flask API Gateway (Port 5000)              │
                   │   • 22-Node LangGraph Cognitive Controller     │
                   └───────────────────────┬────────────────────────┘
                                           │
         ┌─────────────────────────────────┴─────────────────────────────────┐
         ▼                                                                   ▼
┌───────────────────────────────────┐               ┌───────────────────────────────────┐
│   6-Layer Platform Knowledge Base │               │ 9-Node Autonomous ML Pipeline     │
│   • S6: Tenant Isolation          │               │ • Universal ZIP Ingestion Engine  │
│   • S2: Terminology & Acronyms    │               │ • Profiling & Master DAG Selector │
│   • S1: Industrial Ontology (IOF) │               │ • Group-Chronological Splitting   │
│   • S4: Equipment Physics Models  │               │ • Multi-Model Deep HPO Training   │
│   • S5: Standards & Regulatory    │               │ • VG_1 & VG_2 Validation Gates    │
│   • S3: ML Methodology Matching   │               │ • Drift & PSI Deployment Monitor  │
└─────────────────┬─────────────────┘               └─────────────────┬─────────────────┘
                  │                                                   │
                  ▼                                                   ▼
┌───────────────────────────────────┐               ┌───────────────────────────────────┐
│   Infrastructure (Docker)         │               │ Storage & Model Registry          │
│   • PostgreSQL (:5432)            │               │ • MLflow Experiment Tracking      │
│   • Qdrant Vector Engine (:6333)  │               │ • AWS SageMaker Pipeline Bridge   │
│   • MinIO Object Storage (:9000)  │               │                                   │
└───────────────────────────────────┘               └───────────────────────────────────┘
```

---

## 📋 Prerequisites

Before setting up the project, make sure you have the following installed on your machine:

1. **Docker Desktop** (with Docker Compose enabled)
   * Download: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. **Python 3.10 or 3.11**
   * Download: [https://www.python.org/downloads/](https://www.python.org/downloads/)
3. **Node.js (v18.x or v20.x LTS) & npm**
   * Download: [https://nodejs.org/](https://nodejs.org/)
4. **Git** (Windows users: enable long path support)
   ```powershell
   git config --global core.longpaths true
   ```

---

## 🚀 Step-by-Step Setup & Running Guide

### 1. Clone the Repository

```bash
git clone https://github.com/AJ6002/aiconnex-latest.git
cd aiconnex-latest
```

---

### 2. Configure Environment Variables

Copy the safe configuration template:

```bash
# On Linux/macOS
cp .env.example .env

# On Windows (PowerShell)
Copy-Item .env.example .env
```

Open `.env` and configure your API keys (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) if using cloud LLMs. The local Knowledge Base, Qdrant, MinIO, and Postgres will run with default settings out-of-the-box.

---

### 3. Start Infrastructure Services (Docker)

Spin up PostgreSQL, Qdrant Vector Database, and MinIO S3 storage:

```bash
docker compose -f docker-compose.kb.yml up -d
```

Verify all containers are healthy:
```bash
docker ps
```

| Service | Host Port | Internal Port | Description |
|---|---|---|---|
| **PostgreSQL** | `localhost:5432` | 5432 | Platform KB relational schema & tenant store |
| **Qdrant** | `localhost:6333` | 6333 | Vector similarity search engine |
| **MinIO API** | `localhost:9000` | 9000 | S3-compatible raw blob & document storage |
| **MinIO Console** | `localhost:9001` | 9001 | MinIO Web Dashboard (User: `minioadmin` / Pass: `minioadmin`) |

---

### 4. Setup Python Backend & Dependencies

Create a virtual environment and install dependencies:

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

---

### 5. Run the Jane Assistant API Gateway (Backend)

Start the Flask API Gateway for the intelligent chat assistant:

```bash
python chatbot/backend/app.py
```
* **API Gateway URL:** `http://localhost:5000`
* **Health Endpoint:** `http://localhost:5000/health`
* **Chat Endpoint:** `http://localhost:5000/api/v1/jane/chat`

---

### 6. Setup & Start the React Frontend Studio

In a new terminal window:

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

* **Frontend Web App URL:** `http://localhost:3001` (or `http://localhost:3000`)
* **Views available:**
  * 🏠 **Hero Landing View**: Enterprise introduction and quick entry points
  * 📊 **Data Studio / Compiler**: Multi-table ZIP dataset discovery, schema mapping, and joins
  * 🔬 **ML Studio**: 9-Node autonomous model assembly line and training
  * 🧠 **Agent Manager**: 22-Node LangGraph fleet overview and telemetry
  * 💬 **Jane Assistant Modal**: Real-time intelligent industrial RAG chatbot

---

## 🧪 Running Tests & Validation

Run the automated test suite to verify platform health:

```bash
# Run Platform Knowledge Base unit and integration tests
python -m pytest tests/test_platform_kb_context_builder.py tests/test_platform_kb_schemas.py tests/test_platform_kb_embedder.py -v

# Run full test suite
python -m pytest tests/
```

Test the frontend production build:
```bash
cd frontend
npm run build
```

---

## 📚 Repository Layout

```
├── aiconnex_agent/              # 🧠 22-Node LangGraph Brain & Platform KB Services
├── aiconnex_knowledge/          # 📚 17-Tier Active Knowledge Base Architecture
├── aiconnex_ml/                 # 🔬 Core ML Pipeline (Feature Engineering, Training, Eval)
├── aiconnex_zip_compiler/       # 📦 Multi-Table ZIP Ingestion Engine
├── services/                    # ⚙️ 9-Node Microservice Cascade
├── frontend/                    # 🌐 React Web Studio (Vite + TSX + Tailwind)
├── chatbot/                     # 💬 Jane Industrial AI Assistant Engine
├── validation_gate2/            # 🛡️ Dataset Validation Gateway Service
├── sagemaker_pipeline/          # ☁️ AWS Cloud Training Pipeline
├── scripts/                     # 🛠️ Orchestration & Ingestion Utility Scripts
├── tests/                       # ✅ Comprehensive Unit & Integration Test Suite
├── docs/                        # 📖 Consolidated Technical Documentation & Blueprints
│   ├── architecture/            # Technical Architecture Guides
│   ├── specs/                   # Detailed DOCX Blueprints & Schemas
│   ├── research/                # Academic Research Papers
│   ├── executive/               # Presentation Decks & Visual Journals
│   ├── diagrams/                # System Flowcharts & Visual Architecture
│   └── standards/               # ISO & IEC Engineering Standards
├── docker-compose.yml           # 🐳 Microservice Docker Infrastructure
├── docker-compose.kb.yml        # 🐳 Platform KB Infrastructure (Postgres, Qdrant, MinIO)
├── .env.example                 # 📋 Safe Onboarding Environment Template
└── project_snapshot.md          # 📋 Authoritative System Snapshot (v8.0)
```

---

## ❓ Troubleshooting & FAQs

### 1. `Filename too long` error on Windows Git
If git gives a path length error on Windows, run:
```powershell
git config --global core.longpaths true
```

### 2. Port Collisions (e.g., Port 3000 or 5000 already in use)
* **Frontend**: Vite will automatically try port `3001` or `3002` if `3000` is taken.
* **Backend**: Make sure no stale Python process is running on port `5000`. You can check with:
  ```powershell
  netstat -ano | findstr :5000
  ```

### 3. Docker Services Not Responding
If Postgres, Qdrant, or MinIO fail to connect:
```bash
docker compose -f docker-compose.kb.yml down
docker compose -f docker-compose.kb.yml up -d
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
