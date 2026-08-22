"""
Cross-Platform Sandbox Docker Environment Verifier.
"""

import subprocess
import sys


def run_cmd(cmd: str) -> tuple[int, str]:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode, (res.stdout + res.stderr).strip()


def verify_docker_env() -> bool:
    print("=== Level 4 Sandbox: Docker Environment Audit ===")

    # 1. Docker version
    code, out = run_cmd("docker --version")
    if code != 0:
        print("[FAILED] Docker Engine not found:", out)
        return False
    print(f"[OK] Docker Engine: {out}")

    # 2. Buildx version
    code, out = run_cmd("docker buildx version")
    if code != 0:
        print("[FAILED] Docker Buildx not found:", out)
        return False
    print(f"[OK] Docker Buildx: {out}")

    # 3. Test runtime security flags
    test_cmd = (
        "docker run --rm "
        "--network none "
        "--user 10001:10001 "
        "--memory 128m "
        "--cpus 0.5 "
        "--read-only "
        "--tmpfs /tmp "
        "python:3.11-slim "
        "python -c \"print('Sandbox Security Flags OK')\""
    )
    code, out = run_cmd(test_cmd)

    if code != 0:
        print("[FAILED] Security flag verification failed:", out)
        return False

    print(f"[OK] Sandbox Security Flags (--network none, --user 10001:10001, --read-only, memory/cpu): {out}")
    print("=== Docker Environment Audit SUCCESSFUL ===")

    return True


if __name__ == "__main__":
    success = verify_docker_env()
    sys.exit(0 if success else 1)
