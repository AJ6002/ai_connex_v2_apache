"""
hardware.py — GPU/CPU detection, thread/worker management
==========================================================
Used by HPO and training modules to configure n_jobs and device correctly.
"""

from __future__ import annotations
import os


def has_gpu() -> bool:
    """Return True if a CUDA-capable GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        pass
    try:
        import cupy  # type: ignore
        cupy.cuda.Device(0).use()
        return True
    except Exception:
        return False


def cpu_count() -> int:
    """Return the number of available logical CPU cores."""
    return os.cpu_count() or 1


def recommended_n_jobs(cap: int = 8) -> int:
    """
    Return a safe n_jobs value for sklearn parallel operations.
    Caps at `cap` cores to avoid over-subscription on shared machines.
    """
    return min(cpu_count(), cap)


def xgboost_device() -> str:
    """Return 'cuda' if GPU is available, else 'cpu'."""
    return "cuda" if has_gpu() else "cpu"


def lightgbm_device() -> str:
    """Return 'gpu' if GPU is available, else 'cpu'."""
    return "gpu" if has_gpu() else "cpu"
