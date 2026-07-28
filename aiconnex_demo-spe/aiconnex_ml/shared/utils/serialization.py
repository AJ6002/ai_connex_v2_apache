"""
serialization.py — Model export: Pickle, ONNX, Treelite
=========================================================
Exports trained models to the format specified in the manifest's
deployment_target.compilation_format field.

Priority:
  Treelite → fastest batch throughput for tree ensembles on low-power edge
  ONNX     → best cross-language inference for deep learning or mixed models
  Pickle   → default fallback for local/SageMaker
"""

from __future__ import annotations
import os
import pickle
from typing import Any


def save_pickle(model: Any, path: str) -> str:
    """Save a scikit-learn-compatible model to a .pkl file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    print(f"[Serialization] Model saved (pickle): {path}")
    return path


def load_pickle(path: str) -> Any:
    """Load a pickled model from disk."""
    with open(path, "rb") as f:
        return pickle.load(f)


def save_onnx(model: Any, path: str, feature_names: list, n_features: int) -> str:
    """
    Export a scikit-learn model to ONNX format using skl2onnx.
    Falls back to pickle if skl2onnx is not installed.
    """
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        initial_type = [("float_input", FloatTensorType([None, n_features]))]
        onnx_model = convert_sklearn(model, initial_types=initial_type)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        print(f"[Serialization] Model saved (ONNX): {path}")
        return path
    except ImportError:
        print("[Serialization] Warning: skl2onnx not available. Falling back to pickle.")
        pkl_path = path.replace(".onnx", ".pkl")
        return save_pickle(model, pkl_path)


def save_treelite(model: Any, path: str, toolchain: str = "gcc") -> str:
    """
    Compile a tree ensemble model using Treelite.
    Produces a shared library (.so on Linux, .dll on Windows).
    Falls back to pickle if treelite is not installed.
    """
    try:
        import treelite
        import treelite_runtime
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tl_model = treelite.sklearn.import_model(model)
        tl_model.export_lib(toolchain=toolchain, libpath=path, verbose=False)
        print(f"[Serialization] Model compiled (Treelite): {path}")
        return path
    except ImportError:
        print("[Serialization] Warning: treelite not available. Falling back to pickle.")
        pkl_path = path.replace(".so", ".pkl").replace(".dll", ".pkl")
        return save_pickle(model, pkl_path)
    except Exception as e:
        print(f"[Serialization] Treelite compilation failed ({e}). Falling back to pickle.")
        pkl_path = path.replace(".so", ".pkl").replace(".dll", ".pkl")
        return save_pickle(model, pkl_path)


def export_model(
    model: Any,
    path: str,
    format: str = "pickle",
    feature_names: list | None = None,
    n_features: int = 0,
) -> str:
    """
    Unified export entry point. Routes to the correct serializer based on `format`.

    Args:
        model:         Trained model object.
        path:          Desired output path (extension inferred from format).
        format:        One of 'pickle', 'ONNX', 'Treelite'.
        feature_names: Column names (required for ONNX export).
        n_features:    Feature count (required for ONNX export).

    Returns:
        Actual path where the model was saved.
    """
    if format == "ONNX":
        if not path.endswith(".onnx"):
            path = path + ".onnx"
        return save_onnx(model, path, feature_names or [], n_features)
    elif format == "Treelite":
        ext = ".dll" if os.name == "nt" else ".so"
        if not path.endswith(ext):
            path = path + ext
        return save_treelite(model, path)
    else:
        if not path.endswith(".pkl"):
            path = path + ".pkl"
        return save_pickle(model, path)
