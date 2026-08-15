"""
smoke_test.py  --  AIC ML Pipeline Studio
Quick end-to-end test:
  1. Health-check all 8 services
  2. Upload a CSV to the Profiler (port 8000)
  3. POST profile to DAG Orchestrator (port 8001) to start pipeline
  4. Poll status until at least the Prepare step completes
  5. Print the prepared CSV path

Usage:
    python smoke_test.py [path/to/dataset.csv]

If no CSV is provided, searches for built-in test datasets.
Requires all services to be running first:  python start_all.py
"""

import requests
import time
import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVICES = {
    "Dataset Profiler":        8000,
    "DAG Orchestrator":        8001,
    "Recipe Orchestrator":     8002,
    "Prepare API":             8003,
    "Feature Engineering API": 8004,
    "Split API":               8005,
    "Train API":               8006,
    "Evaluate API":            8007,
    "Deploy API":              8008,
}


def p(msg):
    """Print with ASCII fallback for Windows consoles."""
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)


def step(n, total, msg):
    p(f"\n[{n}/{total}] {msg}")


# ---- Step 1: Health Check ---------------------------------------------------

def check_health():
    p("\n=== Health Check ===")
    all_up = True
    for name, port in SERVICES.items():
        try:
            r = requests.get(f"http://127.0.0.1:{port}/api/v1/health", timeout=3)
            if r.status_code == 200:
                p(f"  [OK]   {name} :{port}")
            else:
                p(f"  [WARN] {name} :{port} -> HTTP {r.status_code}")
                all_up = False
        except requests.exceptions.ConnectionError:
            p(f"  [FAIL] {name} :{port} -> OFFLINE")
            all_up = False
    return all_up


# ---- Step 2: Profile Dataset ------------------------------------------------

def profile_dataset(csv_path):
    p(f"  Uploading: {os.path.basename(csv_path)}")
    with open(csv_path, "rb") as f:
        r = requests.post(
            "http://127.0.0.1:8000/api/v1/profile",
            files={"file": (os.path.basename(csv_path), f, "text/csv")},
            timeout=30
        )
    if r.status_code != 200:
        p(f"  [FAIL] Profiler error ({r.status_code}): {r.text[:300]}")
        return None

    data = r.json()
    prof = data["profile"]
    p(f"  [OK]   Profiled successfully")
    p(f"         Rows: {prof.get('num_rows','?')}  |  Cols: {prof.get('num_columns','?')}")
    p(f"         Family: {prof.get('algorithm_family','?')}  |  DAG: {prof.get('recommended_dag_id','?')}")
    p(f"         Target: {prof.get('detected_target','(not detected)')}")
    return prof


# ---- Step 3: Start Pipeline -------------------------------------------------

def start_pipeline(profile):
    r = requests.post(
        "http://127.0.0.1:8001/api/v1/pipeline/run",
        json={"profile": profile},
        timeout=10
    )
    if r.status_code != 200:
        p(f"  [FAIL] Pipeline start failed ({r.status_code}): {r.text[:300]}")
        return None

    data = r.json()
    run_id = data["dag_id"]
    p(f"  [OK]   Pipeline started  --  run_id: {run_id}")
    return run_id


# ---- Step 4: Poll Until Prepare Done ----------------------------------------

def poll_until_done(run_id, timeout=180):
    url = f"http://127.0.0.1:8001/api/v1/pipeline/{run_id}/status"
    logged = 0
    deadline = time.time() + timeout
    progress = 0
    current = ""

    p(f"  Polling pipeline status (max {timeout}s) ...")

    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                p(f"  [WARN] Status poll failed: {r.text[:200]}")
                time.sleep(3)
                continue

            data = r.json()
            logs = data.get("logs", [])
            for entry in logs[logged:]:
                lvl = entry.get("level", "INFO")
                msg = entry.get("message", "")
                ts  = entry.get("timestamp", "")
                p(f"     [{lvl}] {ts}  {msg}")
            logged = len(logs)

            status   = data.get("status")
            progress = data.get("progress_pct", 0)
            current  = data.get("current_step", "")

            if status == "completed":
                results = data.get("results", {})
                p(f"\n  [PASS] Pipeline COMPLETED at {progress}%")
                p(f"         Model:    {results.get('model_name','?')}")
                p(f"         Metrics:  {results.get('metrics', {})}")
                p(f"         Deployed: {results.get('deployed_file','?')}")
                return True, results

            if status == "failed":
                p(f"\n  [FAIL] Pipeline FAILED at step: {current}")
                return False, {}

        except Exception as e:
            p(f"  [WARN] Poll error: {e}")

        time.sleep(2)

    p(f"\n  [TIMEOUT] Stopped polling after {timeout}s  --  Progress: {progress}%  Step: {current}")
    p(f"  Partial results may be available in workspace_data/")
    # Return partial success if prepare is done (progress >= 20)
    return progress >= 20, {"prepared_file": f"workspace_data/prepared_{run_id}.csv", "progress": progress}


# ---- Find Test CSV ----------------------------------------------------------

def find_test_csv():
    candidates = [
        os.path.join(BASE_DIR, "testing_ds", "ds_3", "manufacturing.csv"),
        os.path.join(BASE_DIR, "testing_ds", "ds_4", "equipment_anomaly_data.csv"),
        os.path.join(BASE_DIR, "workspace_data"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
        if os.path.isdir(path):
            for fname in os.listdir(path):
                if fname.endswith(".csv") and not fname.startswith("prepared_") \
                        and not fname.startswith("train_") and not fname.startswith("test_"):
                    return os.path.join(path, fname)
    return None


# ---- Main -------------------------------------------------------------------

if __name__ == "__main__":
    TOTAL = 4
    p("\n" + "=" * 52)
    p("  AIC Pipeline Smoke Test")
    p("=" * 52)

    # Step 1
    step(1, TOTAL, "Health Check -- All Services")
    all_up = check_health()
    if not all_up:
        p("\n  Some services are OFFLINE. Start them first:")
        p(f"      python start_all.py\n")
        sys.exit(1)

    # Step 2
    step(2, TOTAL, "Profile Dataset")
    csv_path = sys.argv[1] if len(sys.argv) > 1 else find_test_csv()
    if not csv_path or not os.path.exists(csv_path):
        p("  [ERROR] No CSV found. Usage:  python smoke_test.py path/to/data.csv")
        sys.exit(1)

    profile = profile_dataset(csv_path)
    if not profile:
        sys.exit(1)

    # Step 3
    step(3, TOTAL, "Start Pipeline (Profile -> DAG -> Recipe -> Prepare -> ...)")
    run_id = start_pipeline(profile)
    if not run_id:
        sys.exit(1)

    # Step 4
    step(4, TOTAL, "Waiting for pipeline to complete ...")
    success, results = poll_until_done(run_id, timeout=180)

    p("\n" + "=" * 52)
    if success:
        p("[PASS]  Smoke test PASSED")
        prepared = results.get("prepared_file", f"workspace_data/prepared_{run_id}.csv")
        p(f"  Prepared CSV : {prepared}")
        p(f"  Full results : {json.dumps(results, indent=2)}")
    else:
        p("[FAIL]  Smoke test FAILED")
        p("  Check service logs for error details.")
    p("=" * 52 + "\n")
