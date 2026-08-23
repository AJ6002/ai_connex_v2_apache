"""
FastAPI Production Intake & Intent Normalizer API.
"""

import hashlib
import importlib
import importlib.util
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from contracts.dataset.dataset_contract import DatasetContract
from contracts.intent.intent_contract import IntentContract

_base_dir = Path(__file__).resolve().parent.parent
_insp_path = _base_dir / "discovery" / "inspector.py"
_insp_spec = importlib.util.spec_from_file_location("inspector_mod", _insp_path)
assert _insp_spec is not None and _insp_spec.loader is not None
_insp_mod = importlib.util.module_from_spec(_insp_spec)
_insp_spec.loader.exec_module(_insp_mod)
inspect_dataset_archive = _insp_mod.inspect_dataset_archive

_norm_path = _base_dir / "intake" / "normalizer.py"
_norm_spec = importlib.util.spec_from_file_location("normalizer_mod", _norm_path)
assert _norm_spec is not None and _norm_spec.loader is not None
_norm_mod = importlib.util.module_from_spec(_norm_spec)
_norm_spec.loader.exec_module(_norm_mod)
normalize_user_intent = _norm_mod.normalize_user_intent


app = FastAPI(
    title="AI-Connex Production Ingestion API",
    version="2.0.0",
    description="Apache-First Dataset Intake & Intent Normalizer Service"
)

UPLOAD_DIR = os.getenv("INTAKE_UPLOAD_DIR", "services/workspace_data/uploads")


class IntentRequest(BaseModel):
    user_goal: str
    tenant_uid: str
    user_uid: str
    site_scope: str | None = None
    asset_scope: str | None = None
    raw_asset_ids: list[str] | None = None


@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "version": "2.0.0"}


@app.get("/metrics")
def metrics_endpoint():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/v2/intake/upload", response_model=DatasetContract)
async def upload_dataset_asset(
    file: UploadFile = File(...),  # noqa: B008
    tenant_uid: str = Form(...),
    site_uid: str | None = Form(None)
):
    """
    HTTP Multipart Ingestion Endpoint.
    Stores raw uploads, hashes binary SHA-256, and extracts member inventory.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_bytes = await file.read()

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    asset_id = f"asset-{sha256_hash[:12]}"
    file_extension = os.path.splitext(file.filename or "")[1] or ".bin"
    saved_filename = f"{asset_id}{file_extension}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(saved_path, "wb") as f:  # noqa: ASYNC230

        f.write(file_bytes)

    member_inventory = [file.filename] if file.filename else ["data.bin"]
    archive_type = "single_file"

    if file_extension.lower() in [".zip", ".tar", ".gz"]:
        discovery = inspect_dataset_archive(saved_path, asset_id)
        member_inventory = discovery.member_inventory
        archive_type = discovery.archive_type

    return DatasetContract(
        asset_id=asset_id,
        tenant_uid=tenant_uid,
        site_uid=site_uid,
        original_filename=file.filename or "unknown",
        file_extension=file_extension,
        mime_type=file.content_type or "application/octet-stream",
        byte_size=len(file_bytes),
        sha256_checksum=sha256_hash,
        storage_uri=saved_path,
        archive_type=archive_type,
        member_inventory=member_inventory
    )


@app.post("/api/v2/intake/normalize", response_model=IntentContract)
def normalize_intent_endpoint(req: IntentRequest):
    """
    Normalize raw user intent text into immutable IntentContract.
    """
    try:
        return normalize_user_intent(
            user_goal=req.user_goal,
            tenant_uid=req.tenant_uid,
            user_uid=req.user_uid,
            site_scope=req.site_scope,
            asset_scope=req.asset_scope,
            raw_asset_ids=req.raw_asset_ids
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to normalize intent: {e!s}") from e
