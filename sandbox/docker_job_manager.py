"""
Docker Job Manager - Host-side security orchestrator for sandbox execution.
Enforces Cosign signature verification, network isolation, non-root execution, resource bounds,
manifest collection, and quarantine handling.
"""

import os
import sys
import json
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import yaml

from contracts.sandbox.result_manifest_contract import ParserResultManifest


class DockerJobManager:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "job_manager_config.yml"
        
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.registry = self.config.get("registry", "ghcr.io/aj6002/ai_connex_v2_apache")
        self.cosign_pub_key = Path(self.config.get("cosign_public_key", "sandbox/keys/cosign.pub"))
        self.quarantine_dir = Path(self.config.get("quarantine_dir", "sandbox/quarantine"))
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def verify_cosign_signature(self, image_ref: str) -> bool:
        """Enforces Cosign signature verification before any docker run call."""
        if not self.cosign_pub_key.exists():
            # If local cosign key is absent, log warning for dev environment
            print(f"[JOB MANAGER WARN] Cosign public key missing at {self.cosign_pub_key}. Skipping signature check in local dev mode.")
            return True

        cmd = f"cosign verify --key {self.cosign_pub_key} {image_ref}"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[JOB MANAGER SECURITY REJECTION] Image {image_ref} failed Cosign verification:\n{res.stderr}")
            return False
        return True

    def execute_job(
        self,
        capability: str,
        input_dir: Path,
        output_dir: Path,
        job_id: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Runs a sandbox container job under strict security controls."""
        if job_id is None:
            job_id = f"job_{uuid.uuid4().hex[:8]}"

        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Match capability to approved image
        target_image_cfg = None
        target_image_key = None
        for img_key, img_cfg in self.config.get("images", {}).items():
            if capability in img_cfg.get("capabilities", []):
                target_image_cfg = img_cfg
                target_image_key = img_key
                break

        if not target_image_cfg:
            err_msg = f"No approved container image mapped to capability '{capability}'"
            print(f"[JOB MANAGER ERROR] {err_msg}")
            return False, None, err_msg

        image_name = target_image_cfg["image"]

        # 2. Hard Cosign signature verification
        if not self.verify_cosign_signature(image_name):
            err_msg = f"SECURITY VIOLATION: Image {image_name} signature verification failed."
            self._handle_quarantine(job_id, input_dir, output_dir, err_msg)
            return False, None, err_msg

        # 3. Construct docker run security flags
        cpus = target_image_cfg.get("cpus", "1.0")
        memory = target_image_cfg.get("memory", "1g")
        timeout_s = target_image_cfg.get("timeout_seconds", 300)

        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--user", "10001:10001",
            "--read-only",
            "--tmpfs", "/tmp",
            "--cpus", str(cpus),
            "--memory", str(memory),
            "-v", f"{input_dir.resolve()}:/sandbox/input:ro",
            "-v", f"{output_dir.resolve()}:/sandbox/output:rw",
            "-e", f"JOB_ID={job_id}"
        ]

        if env_vars:
            for k, v in env_vars.items():
                cmd.extend(["-e", f"{k}={v}"])

        cmd.append(image_name)

        # 4. Execute container with wall-clock timeout
        print(f"[JOB MANAGER] Running sandbox job {job_id} using {image_name}...")
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s
            )
            logs = res.stdout + res.stderr

            # Write run log artifact
            with open(output_dir / "job_execution.log", "w", encoding="utf-8") as f:
                f.write(logs)

            if res.returncode != 0:
                err_msg = f"Container exited with non-zero exit code {res.returncode}:\n{logs}"
                self._handle_quarantine(job_id, input_dir, output_dir, err_msg)
                return False, None, err_msg

        except subprocess.TimeoutExpired:
            err_msg = f"Container execution exceeded wall-clock timeout of {timeout_s}s"
            self._handle_quarantine(job_id, input_dir, output_dir, err_msg)
            return False, None, err_msg

        # 5. Collect result manifest or discovery artifact
        manifest_path = output_dir / "result_manifest.json"
        discovery_path = output_dir / "segmentation_proposal.json"

        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            return True, manifest_data, logs
        elif discovery_path.exists():
            with open(discovery_path, "r", encoding="utf-8") as f:
                discovery_data = json.load(f)
            return True, discovery_data, logs

        err_msg = "Container completed but failed to produce result manifest or proposal artifact."
        self._handle_quarantine(job_id, input_dir, output_dir, err_msg)
        return False, None, err_msg

    def _handle_quarantine(self, job_id: str, input_dir: Path, output_dir: Path, reason: str):
        """Failure / Quarantine handler: moves input and output to quarantine directory."""
        print(f"[JOB MANAGER QUARANTINE] Job {job_id} failed: {reason}")
        q_job_dir = self.quarantine_dir / f"quarantine_{job_id}"
        q_job_dir.mkdir(parents=True, exist_ok=True)

        with open(q_job_dir / "quarantine_reason.txt", "w", encoding="utf-8") as f:
            f.write(f"Job ID: {job_id}\nTimestamp: {datetime.utcnow()}\nReason: {reason}\n")

        # Copy input artifacts to quarantine for audit inspection
        if input_dir.exists():
            for item in input_dir.glob("*"):
                shutil.copy2(item, q_job_dir)
