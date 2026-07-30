"""
H2O Flow Web Dashboard Launcher (Robust Version)
================================================
Launches the H2O-3 in-memory engine and waits for JVM server readiness 
before opening http://127.0.0.1:54321 in your browser.
"""

import sys
import time
import webbrowser
import requests

try:
    import h2o
except ImportError:
    print("[INFO] Package 'h2o' not found. Please run: pip install h2o")
    sys.exit(1)

def is_h2o_ready(url="http://127.0.0.1:54321/flow/index.html", timeout=1):
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False

def main():
    print("=" * 70)
    print("[H2O-3] Starting H2O In-Memory Engine & Flow Web Dashboard...")
    print("=" * 70)

    try:
        # Initialize H2O cluster explicitly binding to 127.0.0.1
        h2o.init(ip="127.0.0.1", port=54321, nthreads=-1, max_mem_size="2G")
    except Exception as e:
        print(f"[H2O-3] Cluster init status/note: {e}")

    flow_url = "http://127.0.0.1:54321"
    
    print("[H2O-3] Waiting for Flow Web Dashboard to become ready...")
    ready = False
    for attempt in range(15):
        if is_h2o_ready():
            ready = True
            break
        time.sleep(1)

    if ready:
        print("\n" + "=" * 70)
        print(f"[SUCCESS] H2O Flow Web Dashboard is LIVE at: {flow_url}")
        print("   1. Open http://127.0.0.1:54321 in your browser.")
        print("   2. Drag & drop dataset CSVs to parse & run AutoML.")
        print("   3. Press Ctrl+C in this terminal window to stop the server.")
        print("=" * 70 + "\n")
        try:
            webbrowser.open(flow_url)
        except Exception:
            pass
    else:
        print(f"\n[INFO] H2O cluster is starting. Try opening {flow_url} in a few seconds.")

    # Keep process alive so H2O JVM stays running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[STOPPING] Shutting down H2O cluster server...")
        try:
            h2o.cluster().shutdown()
        except Exception:
            pass
        print("Done. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
