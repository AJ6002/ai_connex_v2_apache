import requests
import time
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
datasets = [
    os.path.join(BASE_DIR, "testing_ds", "ds_3", "manufacturing.csv"),
    os.path.join(BASE_DIR, "testing_ds", "ds_4", "equipment_anomaly_data.csv"),
]

print("--- Starting Batch Pipeline Run ---")

for ds_path in datasets:
    if not os.path.exists(ds_path):
        print(f"Skipping {ds_path} - file not found.")
        continue

    filename = os.path.basename(ds_path)
    print(f"\n==========================================")
    print(f"Processing dataset: {filename}")
    print(f"==========================================")

    # 1. Profile Dataset
    print(f"Step 1: Profiling dataset via Port 8000...")
    profile_url = "http://127.0.0.1:8000/api/v1/profile"
    
    with open(ds_path, 'rb') as f:
        files = {'file': (filename, f)}
        r_profile = requests.post(profile_url, files=files)
        
    if r_profile.status_code != 200:
        print(f"Error: Profiling failed (status {r_profile.status_code}): {r_profile.text}")
        continue
        
    profile_payload = r_profile.json()
    profile = profile_payload["profile"]
    
    print(f"  Recommended DAG ID: {profile['recommended_dag_id']}")
    print(f"  Detected Target Column: {profile['detected_target']}")
    print(f"  Algorithm Family: {profile['algorithm_family']}")
    print(f"  Suggested Task: {profile['suggested_task']}")

    # 2. Run Pipeline
    print(f"Step 2: Triggering Pipeline execution via Port 8001...")
    run_url = "http://127.0.0.1:8001/api/v1/pipeline/run"
    r_run = requests.post(run_url, json={"profile": profile})
    
    if r_run.status_code != 200:
        print(f"Error: Running pipeline failed (status {r_run.status_code}): {r_run.text}")
        continue
        
    run_payload = r_run.json()
    run_id = run_payload["dag_id"]
    print(f"  Pipeline Run ID: {run_id}")

    # 3. Poll Status
    print(f"Step 3: Polling pipeline execution status...")
    status_url = f"http://127.0.0.1:8001/api/v1/pipeline/{run_id}/status"
    
    # We will poll every 2 seconds
    logged_lines_count = 0
    while True:
        r_status = requests.get(status_url)
        if r_status.status_code != 200:
            print(f"Error: Status poll failed: {r_status.text}")
            break
            
        status_payload = r_status.json()
        status = status_payload["status"]
        progress = status_payload["progress_pct"]
        current_step = status_payload["current_step"]
        logs = status_payload["logs"]

        # Print new logs
        for log in logs[logged_lines_count:]:
            print(f"  [{log['timestamp']}] {log['level']}: {log['message']}")
        logged_lines_count = len(logs)

        if status == "completed":
            print(f"SUCCESS: Pipeline run completed!")
            print(f"  Trained Model: {status_payload['results'].get('model_name')}")
            print(f"  Deployed File: {status_payload['results'].get('deployed_file')}")
            print(f"  Evaluation Metrics: {status_payload['results'].get('metrics')}")
            break
        elif status == "failed":
            print(f"FAILED: Pipeline run failed.")
            break
            
        time.sleep(2)

print("\n--- Batch Pipeline Run Finished ---")
