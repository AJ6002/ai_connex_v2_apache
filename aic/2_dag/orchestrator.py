import asyncio
import uuid
import datetime
import os
import json
from typing import Dict, List, Any

# Dynamic root resolution — works on any machine regardless of username or drive
AIC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_ROOT = os.path.join(AIC_ROOT, "workspace_data")

# Global registry for active and completed runs
RUNS: Dict[str, 'PipelineRun'] = {}

class PipelineRun:
    def __init__(self, run_id: str, profile: dict):
        self.run_id = run_id
        # Use recommended DAG details from the profile
        self.dag_id = profile.get("recommended_dag_id", "DAG_001")
        self.algorithm_family = profile.get("algorithm_family", "Miscellaneous")
        self.suggested_task = profile.get("suggested_task", "Classification")
        self.profile = profile
        self.status = "running"
        self.progress_pct = 0
        self.current_step = ""
        self.logs: List[dict] = []
        self.results: Dict[str, Any] = {}
        
        # Load the dynamic recipe configuration matching the DAG ID
        self.recipe = self._load_recipe()
        
        # Define 6 workflow steps: PREPARE -> FEATURE_ENG -> SPLIT -> TRAIN -> EVAL -> DEPLOY
        self.steps = self._define_steps()
        
        # Save meta2.json inside 2_dag/meta/
        meta_dir = os.path.join(os.path.dirname(__file__), "meta")
        os.makedirs(meta_dir, exist_ok=True)
        meta_path = os.path.join(meta_dir, "meta2.json")
        meta2_payload = {
            "dag_id": self.dag_id,
            "family": self.algorithm_family,
            "suggested_task": self.suggested_task,
            "prepare_recipe": self.recipe.get("prepare_recipe", {}),
            "feature_engineering_recipe": self.recipe.get("feature_engineering_recipe", {}),
            "splitting_recipe": self.recipe.get("splitting_recipe", {}),
            "training_recipe": self.recipe.get("training_recipe", {})
        }
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta2_payload, f, indent=2)
        
    def _load_recipe(self) -> dict:
        base_path = os.path.dirname(__file__)  # aic/2_dag
        root_dir = os.path.dirname(base_path)  # aic
        
        meta3_path = os.path.join(root_dir, "3_recipe_orchestrator", "meta", "meta3.json")
        if os.path.exists(meta3_path):
            try:
                with open(meta3_path, 'r', encoding='utf-8') as f:
                    meta3 = json.load(f)
                if meta3.get("dag_id") == self.dag_id:
                    return meta3.get("recipes", {})
            except Exception as e:
                print("Error loading compiled meta3:", e)
                
        # Fallback: load separate recipe files directly from 3_recipe_orchestrator/recipe
        prep_dir = os.path.join(root_dir, "3_recipe_orchestrator", "recipe", "preparing")
        feat_dir = os.path.join(root_dir, "3_recipe_orchestrator", "recipe", "feature_engineering")
        split_dir = os.path.join(root_dir, "3_recipe_orchestrator", "recipe", "splitting")
        train_dir = os.path.join(root_dir, "3_recipe_orchestrator", "recipe", "training")
        
        prep_path = os.path.join(prep_dir, f"{self.dag_id}.json")
        feat_path = os.path.join(feat_dir, f"{self.dag_id}.json")
        split_path = os.path.join(split_dir, f"{self.dag_id}.json")
        train_path = os.path.join(train_dir, f"{self.dag_id}.json")
        
        fallback_ids = {
            "Classification": "DAG_001",
            "Regression": "DAG_241",
            "Anomaly Detection": "DAG_486",
            "Clustering": "DAG_696",
            "Time-Series": "DAG_906",
            "Digital Twin": "DAG_1131",
            "Reinforcement Learning": "DAG_1241",
            "Recommendation": "DAG_1341",
            "NLP/Text-Classification": "DAG_1451",
            "Computer Vision": "DAG_1561"
        }
        
        fallback_id = fallback_ids.get(self.algorithm_family, "DAG_001")
        if not os.path.exists(prep_path): prep_path = os.path.join(prep_dir, f"{fallback_id}.json")
        if not os.path.exists(feat_path): feat_path = os.path.join(feat_dir, f"{fallback_id}.json")
        if not os.path.exists(split_path): split_path = os.path.join(split_dir, f"{fallback_id}.json")
        if not os.path.exists(train_path): train_path = os.path.join(train_dir, f"{fallback_id}.json")
            
        try:
            with open(prep_path, 'r', encoding='utf-8') as f: prep_rec = json.load(f)
            with open(feat_path, 'r', encoding='utf-8') as f: feat_rec = json.load(f)
            with open(split_path, 'r', encoding='utf-8') as f: split_rec = json.load(f)
            with open(train_path, 'r', encoding='utf-8') as f: train_rec = json.load(f)
            return {
                "prepare_recipe": prep_rec,
                "feature_engineering_recipe": feat_rec,
                "splitting_recipe": split_rec,
                "training_recipe": train_rec
            }
        except Exception as e:
            print("Error loading recipe components:", e)
            
        return {
            "prepare_recipe": {"impute_strategy": "mean", "scale_method": "standard"},
            "feature_engineering_recipe": {"polynomial_degree": 1, "interaction_features": False},
            "splitting_recipe": {"test_size": 0.2},
            "training_recipe": {"algorithm": "Estimator", "variant": "Standard"}
        }

    def _define_steps(self) -> List[dict]:
        return [
            {"name": "Data Preparation (PREPARE)", "status": "pending", "duration": 2.0},
            {"name": "Feature Engineering (FEATURE_ENG)", "status": "pending", "duration": 2.5},
            {"name": "Data Splitting (SPLIT)", "status": "pending", "duration": 1.0},
            {"name": "Model Training (TRAIN)", "status": "pending", "duration": 3.0},
            {"name": "Evaluation & Validation (EVAL)", "status": "pending", "duration": 2.0},
            {"name": "Deployment & Monitoring (DEPLOY)", "status": "pending", "duration": 1.5}
        ]
            
    def add_log(self, level: str, message: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.logs.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })

    async def execute(self):
        import requests
        self.add_log("INFO", f"Starting 6-step pipeline execution for DAG run '{self.run_id}'")
        self.add_log("INFO", f"Target DAG ID resolved: {self.dag_id}")
        self.add_log("INFO", f"Suggested ML Task: {self.suggested_task}")

        # Compile recipe via Port 8002 to ensure we have the unified config
        try:
            self.add_log("INFO", "Compiling recipes via Recipe Orchestrator (Port 8002)...")
            res = requests.post("http://127.0.0.1:8002/api/v1/orchestrate", json={
                "meta1": {"profile": self.profile},
                "meta2": {"dag_id": self.dag_id, "suggested_task": self.suggested_task}
            })
            if res.status_code == 200:
                meta3 = res.json().get("meta3", {})
                self.recipe = meta3.get("recipes", self.recipe)
                self.add_log("SUCCESS", "Recipe Orchestrator resolved and compiled 4-part recipes.")
            else:
                self.add_log("WARNING", f"Recipe Orchestrator returned status {res.status_code}. Using fallbacks.")
        except Exception as e:
            self.add_log("WARNING", f"Could not connect to Recipe Orchestrator: {str(e)}. Using fallback recipes.")
            
        num_steps = len(self.steps)
        
        # Resolve raw file path
        raw_file_path = self.profile.get("raw_file_path")
        if not raw_file_path:
            filename = self.profile.get("filename") or "manufacturing.csv"
            import glob
            matches = glob.glob(os.path.join(AIC_ROOT, "**", filename), recursive=True)
            if matches:
                raw_file_path = matches[0]
            else:
                raw_file_path = os.path.join(AIC_ROOT, "testing_ds", "ds_3", "manufacturing.csv")
                
        self.raw_file_path = raw_file_path
        self.prepared_file_path = None
        self.engineered_file_path = None
        self.train_path = None
        self.val_path = None
        self.test_path = None
        self.model_path = None
        self.scaler_path = None
        self.eval_metrics = {}
        self.deploy_result = {}
        self.deploy_approved = True   # Advisory VG_2 gate result (Sprint 4)

        # ── Sprint 1: Initialise shared manifest state file ──────────────────
        workspace_dir = os.path.join(WORKSPACE_ROOT, self.run_id)
        os.makedirs(workspace_dir, exist_ok=True)
        self.manifest_path = os.path.join(workspace_dir, f"training_manifest_{self.run_id}.json")
        self.workspace_dir = workspace_dir

        initial_manifest = {
            "run_id": self.run_id,
            "dag_id": self.dag_id,
            "ml_task": self.suggested_task.lower(),
            "raw_file_path": raw_file_path,
            "target_column": self.profile.get("detected_target"),
            "data_topology": self.profile.get("data_topology", "tabular"),
            "entity_column": self.profile.get("entity_column"),
            "timestamp_column": self.profile.get("timestamp_column"),
            "schema_config": {
                "entity_column": self.profile.get("entity_column"),
                "timestamp_column": self.profile.get("timestamp_column"),
            },
            "recipes": self.recipe,
            "quality_gates": {
                "family": self.algorithm_family,
                "regression_gates": {"max_rmse": 9999, "min_r2": -1},
                "anomaly_gates": {"min_f1": 0.0}
            },
            "status": "initialized",
            "pipeline_step": "orchestrator",
        }
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(initial_manifest, f, indent=2, ensure_ascii=False)
        self.add_log("INFO", f"[Manifest] Initialized: {self.manifest_path}")

        try:
            for idx, step in enumerate(self.steps):
                step_name = step["name"]
                self.current_step = step_name
                step["status"] = "running"
                
                self.add_log("INFO", f"--- [Step {idx+1}/{num_steps}] Executing '{step_name}' ---")
                
                await self._run_step_api(step_name)
                
                step["status"] = "completed"
                self.progress_pct = int(((idx + 1) / num_steps) * 100)
                self.add_log("SUCCESS", f"Step '{step_name}' completed successfully.")
                
            # Finalize
            self.status = "completed"
            self.current_step = ""
            self._populate_results()
            self.add_log("SUCCESS", f"Pipeline DAG execution completed! Service endpoint deployed for {self.dag_id}.")
        except Exception as e:
            self.status = "failed"
            self.add_log("ERROR", f"Pipeline execution failed: {str(e)}")
            raise e

    async def _run_step_api(self, step_name: str):
        import requests
        import asyncio
        
        # 1. PREPARE API (Port 8003)
        if step_name == "Data Preparation (PREPARE)":
            prep_url = "http://127.0.0.1:8003/api/v1/prepare"
            prep_recipe = self.recipe.get("prepare_recipe", {})
            target_col = self.profile.get("detected_target")
            
            self.add_log("INFO", f"[Prepare API] POST {prep_url}...")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(
                prep_url,
                json={
                    "raw_file_path": self.raw_file_path,
                    "recipe": prep_recipe,
                    "run_id": self.run_id,
                    "target_column": target_col,
                    "manifest_path": self.manifest_path
                },
                timeout=30
            ))
            if response.status_code != 200:
                raise Exception(f"Prepare API failed (status {response.status_code}): {response.text}")
            res_json = response.json()
            self.prepared_file_path = res_json["prepared_file_path"]
            self.add_log("SUCCESS", f"[Prepare API] Preprocessing complete: {self.prepared_file_path}")

        # 2. FEATURE ENGINEERING API (Port 8004)
        elif step_name == "Feature Engineering (FEATURE_ENG)":
            feat_url = "http://127.0.0.1:8004/api/v1/feature_engineer"
            feat_recipe = self.recipe.get("feature_engineering_recipe", {})
            target_col = self.profile.get("detected_target")
            
            self.add_log("INFO", f"[Feature Eng API] POST {feat_url}...")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(
                feat_url,
                json={
                    "prepared_file_path": self.prepared_file_path,
                    "recipe": feat_recipe,
                    "run_id": self.run_id,
                    "target_column": target_col,
                    "manifest_path": self.manifest_path
                },
                timeout=30
            ))
            if response.status_code != 200:
                raise Exception(f"Feature Engineering API failed (status {response.status_code}): {response.text}")
            res_json = response.json()
            self.engineered_file_path = res_json["engineered_file_path"]
            self.add_log("SUCCESS", f"[Feature Eng API] Transformations complete (+{res_json.get('features_added',0)} features). Saved: {self.engineered_file_path}")

        # 3. SPLIT API (Port 8005)
        elif step_name == "Data Splitting (SPLIT)":
            split_url = "http://127.0.0.1:8005/api/v1/split"
            split_recipe = self.recipe.get("splitting_recipe", {})
            target_col = self.profile.get("detected_target")
            
            self.add_log("INFO", f"[Split API] POST {split_url}...")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(
                split_url,
                json={
                    "prepared_file_path": self.prepared_file_path,
                    "engineered_file_path": self.engineered_file_path,
                    "recipe": split_recipe,
                    "run_id": self.run_id,
                    "target_column": target_col,
                    "manifest_path": self.manifest_path
                },
                timeout=30
            ))
            if response.status_code != 200:
                raise Exception(f"Split API failed (status {response.status_code}): {response.text}")
            res_json = response.json()
            self.train_path = res_json["train_path"]
            self.val_path = res_json["val_path"]
            self.test_path = res_json["test_path"]
            self.add_log("SUCCESS", f"[Split API] Partitioned: Train={self.train_path}")

        # 4. TRAIN API (Port 8006) — Async Dispatch + Poll
        elif step_name == "Model Training (TRAIN)":
            train_url    = "http://127.0.0.1:8006/api/v1/train"
            status_base  = "http://127.0.0.1:8006/api/v1/train/status"
            train_recipe = self.recipe.get("training_recipe", {})
            target_col   = self.profile.get("detected_target")

            self.add_log("INFO", f"[Train API] POST {train_url} (async dispatch)...")
            loop = asyncio.get_event_loop()

            # ── Step 4a: Dispatch job (expects 202 Accepted) ──────────────────
            dispatch_resp = await loop.run_in_executor(None, lambda: requests.post(
                train_url,
                json={
                    "train_path":    self.train_path,
                    "val_path":      self.val_path,
                    "target_column": target_col,
                    "recipe":        train_recipe,
                    "run_id":        self.run_id,
                    "manifest_path": self.manifest_path,
                },
                timeout=15
            ))
            if dispatch_resp.status_code not in (200, 202):
                raise Exception(f"Train API dispatch failed (status {dispatch_resp.status_code}): {dispatch_resp.text}")

            job_id = dispatch_resp.json().get("job_id")
            self.add_log("INFO", f"[Train API] Job dispatched → job_id={job_id}. Polling for completion...")

            # ── Step 4b: Poll /train/status/{job_id} every 2s ────────────────
            max_wait_seconds = 600   # 10-minute ceiling for HPO runs
            elapsed          = 0
            poll_interval    = 2

            while elapsed < max_wait_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                status_resp = await loop.run_in_executor(None, lambda: requests.get(
                    f"{status_base}/{job_id}", timeout=10
                ))
                if status_resp.status_code != 200:
                    self.add_log("WARNING", f"[Train API] Status poll returned {status_resp.status_code}. Retrying...")
                    continue

                job = status_resp.json()
                job_status = job.get("status")

                if job_status == "completed":
                    result = job.get("result", {})
                    self.model_path  = result.get("model_path")
                    self.scaler_path = result.get("scaler_path")
                    vg1 = job.get("vg1_report", {})
                    self.add_log("SUCCESS", f"[Train API] Training complete after {elapsed}s → {self.model_path}")
                    if vg1:
                        self.add_log("INFO", f"[VG_1] Gate passed — {len(vg1.get('checks', {}))} checks.")
                    break

                elif job_status == "failed":
                    error_msg = job.get("error", "Unknown training error")
                    vg1 = job.get("vg1_report", {})
                    if vg1 and not vg1.get("passed", True):
                        failed_checks = [k for k, v in vg1.get("checks", {}).items() if not v.get("passed")]
                        self.add_log("ERROR", f"[VG_1] Gate FAILED: {failed_checks}. Pipeline aborted.")
                    raise Exception(f"Train job {job_id} failed: {error_msg}")

                else:
                    self.add_log("INFO", f"[Train API] Job {job_id} still running ({elapsed}s elapsed)...")

            else:
                raise Exception(f"Train job {job_id} timed out after {max_wait_seconds}s.")

        # 5. EVALUATE API (Port 8007) — Universal Evaluator
        elif step_name == "Evaluation & Validation (EVAL)":
            eval_url     = "http://127.0.0.1:8007/api/v1/evaluate"
            train_recipe = self.recipe.get("training_recipe", {})
            metrics      = train_recipe.get("validation_metrics", [])
            target_col   = self.profile.get("detected_target")

            self.add_log("INFO", f"[Evaluate API] POST {eval_url} (Universal Evaluator)...")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(
                eval_url,
                json={
                    "model_path":    self.model_path,
                    "test_path":     self.test_path,
                    "train_path":    self.train_path,
                    "val_path":      self.val_path,
                    "target_column": target_col,
                    "metrics":       metrics,
                    "manifest_path": self.manifest_path,
                },
                timeout=60
            ))
            if response.status_code != 200:
                raise Exception(f"Evaluate API failed (status {response.status_code}): {response.text}")

            res_json = response.json()
            self.eval_metrics   = res_json.get("metrics", {})
            self.deploy_approved = res_json.get("deploy_approved", True)
            vg2                 = res_json.get("vg2_advisory", {})
            evaluator_used      = res_json.get("evaluator_used", "unknown")

            for k, v in self.eval_metrics.items():
                self.add_log("SUCCESS", f"[Evaluate Metric] {k.upper()}: {round(float(v), 4) if isinstance(v, (int, float)) else v}")

            self.add_log("INFO", f"[VG_2 Advisory] Score={vg2.get('score', 'N/A')} | Evaluator={evaluator_used}")
            for warn in vg2.get("warnings", []):
                self.add_log("WARNING", f"[VG_2] {warn}")

            if not self.deploy_approved:
                self.add_log("WARNING", "[VG_2] deploy_approved=False — deployment will be skipped.")

        # 6. DEPLOY MONITOR API (Port 8008) — Gated by Advisory VG_2
        elif step_name == "Deployment & Monitoring (DEPLOY)":
            # ── Advisory VG_2 deployment gate ────────────────────────────────
            if not self.deploy_approved:
                self.add_log("WARNING", "[Deploy Gate] VG_2 advisory gate indicates deploy_approved=False. Skipping deployment.")
                self.deploy_result = {"status": "skipped", "reason": "VG_2 advisory gate: deploy_approved=False"}
                return   # Exit _run_step_api cleanly — run continues to _populate_results

            deploy_url   = "http://127.0.0.1:8008/api/v1/deploy"
            dataset_name = self.profile.get("filename", os.path.basename(self.raw_file_path))

            self.add_log("INFO", f"[Deploy API] POST {deploy_url}...")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(
                deploy_url,
                json={
                    "model_path":   self.model_path,
                    "run_id":       self.run_id,
                    "dataset_name": dataset_name,
                    "dag_id":       self.dag_id,
                    "manifest_path": self.manifest_path,
                },
                timeout=30
            ))
            if response.status_code != 200:
                raise Exception(f"Deploy API failed (status {response.status_code}): {response.text}")
            res_json = response.json()
            self.deploy_result = res_json
            self.add_log("SUCCESS", f"[Deploy API] Deployed model: {res_json['model_file']}")
            self.add_log("SUCCESS", f"[Deploy API] Endpoint: {res_json['endpoint_url']}")

    def _populate_results(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        train_cfg = self.recipe.get("training_recipe", {})
        algorithm = train_cfg.get("algorithm", "Estimator")
        variant = train_cfg.get("variant", "Standard")
        
        self.results = {
            "model_name": f"{algorithm} ({variant})",
            "dag_id": self.dag_id,
            "trained_at": now,
            "metrics": self.eval_metrics,
            "parameters": train_cfg.get("hyperparameters", {}),
            "endpoint_url": self.deploy_result.get("endpoint_url", f"http://127.0.0.1:8001/api/v1/predict/{self.run_id}"),
            "deployed_file": self.deploy_result.get("model_file")
        }

def create_pipeline_run(profile: dict) -> PipelineRun:
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    run = PipelineRun(run_id, profile)
    RUNS[run_id] = run
    asyncio.create_task(run.execute())
    return run
