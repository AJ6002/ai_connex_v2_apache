import subprocess
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(BASE_DIR, "frontend")

print("Launching frontend dev server via Python subprocess...", flush=True)
p = subprocess.Popen(
    ["npm.cmd", "run", "dev"],
    cwd=frontend_dir
)
try:
    p.wait()
except KeyboardInterrupt:
    p.terminate()
