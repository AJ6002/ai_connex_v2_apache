"""
Data Studio Job Manager & Docker Sandbox Executor.
Manages container lifecycles with strict resource limits and network isolation.
"""

import os
import subprocess
from typing import Dict, Any, List, Optional

class DockerJobManager:
    def __init__(self, default_memory_limit: str = "1g", default_cpu_limit: str = "2.0"):
        self.memory_limit = default_memory_limit
        self.cpu_limit = default_cpu_limit

    def build_container_command(
        self,
        image_tag: str,
        input_host_path: str,
        output_host_dir: str,
        container_input_path: str = "/home/appuser/app/input_file",
        container_output_dir: str = "/home/appuser/app/output"
    ) -> List[str]:
        """
        Build isolated docker run command arguments.
        """
        os.makedirs(output_host_dir, exist_ok=True)
        abs_input = os.path.abspath(input_host_path)
        abs_output = os.path.abspath(output_host_dir)

        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--user", "10001:10001",
            "--memory", self.memory_limit,
            "--cpus", self.cpu_limit,
            "-v", f"{abs_input}:{container_input_path}:ro",
            "-v", f"{abs_output}:{container_output_dir}:rw",
            image_tag,
            container_input_path,
            container_output_dir
        ]
        return cmd

    def run_parser_job(self, image_tag: str, input_path: str, output_dir: str, timeout_seconds: int = 120) -> Dict[str, Any]:
        """
        Execute single-purpose container job within security sandbox.
        """
        cmd = self.build_container_command(image_tag, input_path, output_dir)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
            return {
                "success": res.returncode == 0,
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "error": f"Job execution timed out after {timeout_seconds}s"
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "error": str(e)
            }
