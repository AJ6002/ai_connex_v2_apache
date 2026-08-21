"""
FastAPI Production Intake & Intent Normalizer API.
"""

import os
import hashlib
import uuid
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from contracts.dataset.dataset_contract import DatasetContract
from contracts.intent.intent_contract import IntentContract
from data-studio.discovery.inspector import inspect_dataset_archive
from data-studio.intake.normalizer import normalize_user_intent

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
    site_scope: Optional[str] = None
    asset_scope: Optional[str] = None
    raw_asset_ids: Optional[List[str]] = None

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "version": "2.0.0"}

@app.post("/api/v2/intake/upload", response_model=DatasetContract)
async def upload_dataset_asset(
    file: UploadFile = File(...),
    tenant_uid: str = Form(...),
    site_uid: Optional[str] = Form(None)
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    asset_id = f"asset-{uuid.uuid4().hex[:8]}"
    file_path = os.path.join(UPLOAD_DIR, f"{asset_id}_{file.filename}")

    hasher = hashlib.sha256()
    size_bytes = 0

    with open(file_path, "wb") as buffer:
        while chunk := await file.read(8192):
            size_bytes += len(chunk)
            hasher.update(chunk)
            buffer.write(chunk)

    sha256_hash = hasher.hexdigest()

    # Perform safe lightweight inspection
    discovery = inspect_dataset_archive(file_path, asset_id)
    if not discovery.is_safe:
        raise HTTPException(status_code=400, detail=f"Archive rejected: {discovery.security_findings}")

    fmt = file.filename.split(".")[-1].lower()

    contract = DatasetContract(
        asset_id=asset_id,
        tenant_uid=tenant_uid,
        site_uid=site_uid,
        asset_name=file.filename,
        storage_uri=f"file://{os.path.abspath(file_path)}",
        format=fmt,
        size_bytes=size_bytes,
        sha256_hash=sha256_hash,
        status="PARSED" if discovery.is_safe else "QUARANTINED"
    )

    return contract

@app.post("/api/v2/intake/intent", response_model=IntentContract)
def process_user_intent(req: IntentRequest):
    intent_envelope = normalize_user_intent(
        user_goal=req.user_goal,
        tenant_uid=req.tenant_uid,
        user_uid=req.user_uid,
        site_scope=req.site_scope,
        asset_scope=req.asset_scope,
        raw_asset_ids=req.raw_asset_ids
    )
    return intent_envelope
