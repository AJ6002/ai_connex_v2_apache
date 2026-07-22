"""
start_all.py  --  AIC ML Pipeline Studio
Launches all 8 microservices using the shared .venv from 1_dataset_profiler.

Usage:
    python start_all.py

Stop:
    Ctrl+C
"""

import subprocess
import time
import sys
import os
import threading
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = "python"

SERVICES = [
    {"name": "Dataset Profiler",        "path": "1_dataset_profiler/main.py",     "port": 8000},
    {"name": "DAG Orchestrator",        "path": "2_dag/main.py",                  "port": 8001},
    {"name": "Recipe Orchestrator",     "path": "3_recipe_orchestrator/main.py",  "port": 8002},
    {"name": "Prepare API",             "path": "4_prepare/main.py",              "port": 8003},
    {"name": "Feature Engineering API", "path": "5_feature_engineering/main.py", "port": 8004},
    {"name": "Split API",               "path": "6_split/main.py",                "port": 8005},
    {"name": "Train API",               "path": "7_train/main.py",                "port": 8006},
    {"name": "Evaluate API",            "path": "8_evaluate/main.py",             "port": 8007},
    {"name": "Deploy API",              "path": "9_deploy_monitor/main.py",       "port": 8008},
]

# Ensure workspace_data directory exists for all services
os.makedirs(os.path.join(BASE_DIR, "workspace_data"), exist_ok=True)


def safe_print(msg):
    """Print, gracefully ignoring encoding errors on Windows console."""
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)


def stream_output(name, pipe, prefix=""):
    """Stream subprocess output to console with service name prefix (threaded)."""
    for line in iter(pipe.readline, ""):
        if line:
            safe_print(f"[{name}] {prefix}{line.rstrip()}")


def launch_service(svc):
    full_path = os.path.join(BASE_DIR, svc["path"])
    script_dir = os.path.dirname(full_path)
    script_name = os.path.basename(full_path)
    name = svc["name"]
    port = svc["port"]

    safe_print(f"  >> Launching {name} on port {port} ...")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["AIC_RELOAD"] = os.environ.get("AIC_RELOAD", "0")
    p = subprocess.Popen(
        [VENV_PYTHON, script_name],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
        env=env
    )

    # Stream stdout and stderr in background threads
    threading.Thread(target=stream_output, args=(name, p.stdout), daemon=True).start()
    threading.Thread(target=stream_output, args=(name, p.stderr, "ERR "), daemon=True).start()

    return p


def check_services_alive(processes):
    """After a brief startup pause, report which services are alive."""
    time.sleep(5)
    safe_print("\n--- Startup Status ---")
    all_ok = True
    for svc, p in processes:
        if p.poll() is not None:
            safe_print(f"  [FAIL] {svc['name']} died (exit code {p.returncode})")
            safe_print(f"         Check the [ERR] lines above for details.")
            all_ok = False
        else:
            safe_print(f"  [ OK ] {svc['name']}  ->  http://127.0.0.1:{svc['port']}")
    if all_ok:
        safe_print("\n  All 9 services are running!")
        safe_print(f"  Dashboard: file:///{os.path.join(BASE_DIR, 'main_dashboard', 'index.html')}")
        safe_print(f"  Smoke test: python smoke_test.py path/to/data.csv")
    else:
        safe_print("\n  WARNING: Some services failed to start.")
        safe_print("  Run individual services manually to diagnose:")
        safe_print(f"  Example: cd 4_prepare && {VENV_PYTHON} main.py")
    safe_print("")


if __name__ == "__main__":
    safe_print("=" * 60)
    safe_print("  AIC ML Pipeline Studio -- Starting All Services")
    safe_print("=" * 60)

    if not shutil.which(VENV_PYTHON):
        safe_print(f"\n[ERROR] Python interpreter '{VENV_PYTHON}' not found on system PATH.")
        sys.exit(1)

    processes = []
    for svc in SERVICES:
        p = launch_service(svc)
        processes.append((svc, p))
        time.sleep(1.0)

    safe_print("\n  All services launched. Status check in 4 seconds...")
    safe_print("  Press Ctrl+C to stop.\n")

    # Health check runs in background so log output is not blocked
    threading.Thread(target=check_services_alive, args=(processes,), daemon=True).start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        safe_print("\n\nShutting down all services...")
        for svc, p in processes:
            p.terminate()
            safe_print(f"  Stopped {svc['name']}")
        safe_print("Done.\n")
