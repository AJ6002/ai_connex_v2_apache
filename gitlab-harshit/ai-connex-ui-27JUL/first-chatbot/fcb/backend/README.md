# AI Connexx Chatbot Backend (Flask)

Implements the intent-recognition backend discussed for the AI Connexx chat
assistant: structured intent/entity extraction, schema + state validation,
confidence-based routing, and dispatch to the (stubbed) dataset profiler /
DAG execution / recipe orchestrator pipeline.

## Files

| File | Responsibility |
|---|---|
| `intents.py` | The intent taxonomy: every intent, its risk tier, description, and example phrasings. **Edit this first** when adding new capabilities. |
| `schemas.py` | Pydantic models for the extraction output (`ExtractedIntent`) and validation result (`ValidationOutcome`). |
| `extraction.py` | Calls Gemini with structured-output mode to turn a prompt into `{intent, entities, confidence}`. Falls back to a keyword-based simulator if `GEMINI_API_KEY` isn't set, so you can run everything below without a live key. |
| `pipeline_state.py` | Stand-in for your real dataset/DAG registry. Currently an in-memory dict (`_FAKE_REGISTRY`) -- **replace the function bodies here** with real calls into your Validation_Gateway backend once ready. Nothing else needs to change. |
| `validation.py` | The deterministic gate: checks required entities are present, the dataset exists, prerequisite stages are complete, and flags high-impact intents as needing confirmation. |
| `dispatcher.py` | Routes a validated intent to a reply, and (today) simulates triggering the actual meta1/meta2/meta3 stage. Replace the `# TODO` lines with real calls into your profiler/DAG/recipe services. |
| `app.py` | Flask app. Exposes `POST /api/chat` (same request/response shape as the existing Express route, so `MainChatView.tsx` needs no changes) and `GET /api/health`. |

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY, or leave blank to use the fallback simulator
python app.py
```

The server listens on `http://localhost:5000` (or `$PORT`).

## Wiring it to the existing frontend

The current frontend (`ai-connexx-suite`) calls `/api/chat` through the Express
dev server. Two ways to point it at this Flask backend instead:

1. **Vite proxy (recommended, no frontend code changes)** -- in `vite.config.ts`, add:
   ```ts
   server: {
     proxy: { '/api': 'http://localhost:5000' }
   }
   ```
   Then stop using the Express `/api/chat` route (or just don't call it) and run this Flask server alongside `npm run dev`.

2. **Direct CORS** -- point `fetch('/api/chat')` in `MainChatView.tsx` at `http://localhost:5000/api/chat`, and add `flask-cors`:
   ```python
   from flask_cors import CORS
   CORS(app)
   ```

## How a request flows (matches the architecture discussed earlier)

1. `POST /api/chat` receives `{message, history, conversationId}`.
2. If there's a pending high-impact confirmation for this `conversationId`, a plain "yes"/"no" is handled first.
3. Otherwise, `extraction.extract_intent()` returns intent + entities + confidence.
4. Confidence routing: low confidence -> "please rephrase"; medium -> ask a clarifying question; high -> proceed.
5. `validation.validate()` checks required entities, dataset existence, and stage prerequisites.
6. High-impact intents (currently just `deploy_pipeline`) require an explicit "yes" before dispatch.
7. `dispatcher.dispatch()` returns the reply text plus `topologyAssigned` / `dagMatched` / `recipeCompiled` booleans reflecting real (simulated) state -- these map directly onto the badges already in `MainChatView.tsx`.

## Extending the intent taxonomy

To add a new intent (e.g. a "Data Sanitization & Cleaning" action matching another sidebar tab):

1. Add an entry to `INTENT_TAXONOMY` in `intents.py` with its risk tier, description, examples, and required entities.
2. Add a branch in `dispatcher.dispatch()` for the new intent.
3. If it depends on a prior stage, add it to `PREREQUISITES` in `validation.py`.
4. If it's high-impact, no extra work needed -- the confirmation flow in `app.py` already handles any intent whose risk tier is `high_impact`.

## What's stubbed vs. real

- **Real**: the extraction call to Gemini (once `GEMINI_API_KEY` is set), the Pydantic validation, the confidence-routing logic, the confirmation flow, the Flask route shape.
- **Stubbed (by design, to be replaced)**: `pipeline_state.py`'s in-memory registry, and the `# TODO` lines in `dispatcher.py` that currently just flip booleans instead of calling your real Dataset Profiler / DAG Execution / Recipe Orchestrator services.
