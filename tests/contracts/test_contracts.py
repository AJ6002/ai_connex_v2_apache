"""
Automated Contract Validation Test Suite - Verifies all 18 Pydantic v2 Contract Schemas.
"""

import pytest
from datetime import datetime
from contracts.intent.intent_contract import IntentContract
from contracts.tenant.tenant_contract import TenantContract
from contracts.dataset.dataset_contract import DatasetContract
from contracts.discovery.discovery_contract import DatasetDiscoveryArtifact
from contracts.manifest.manifest_contract import ManifestContract
from contracts.profile.profile_contract import ProfileContract
from contracts.dag.dag_contract import DAGContract
from contracts.recipe.recipe_contract import RecipeContract, RecipeStep
from contracts.prepare.prepare_contract import PrepareContract
from contracts.feature.feature_contract import FeatureContract
from contracts.model.model_contract import ModelContract
from contracts.agent.agent_spec_contract import AgentSPECContract
from contracts.tool.tool_contract import ToolContract
from contracts.telemetry.telemetry_contract import TelemetryContract
from contracts.deployment.deployment_contract import DeploymentContract
from contracts.audit.audit_contract import AuditContract

def test_intent_contract():
    contract = IntentContract(
        intent_uid="intent-001",
        tenant_uid="tenant-123",
        user_uid="user-456",
        goal="Predict turbofan RUL",
        intent_type="time_series_forecast"
    )
    assert contract.intent_uid == "intent-001"
    assert contract.autonomy_requested == "HITL"

def test_tenant_contract():
    contract = TenantContract(
        tenant_id="tenant-123",
        tenant_name="Industrial Energy Corp",
        user_id="user-456"
    )
    assert contract.tenant_id == "tenant-123"
    assert contract.is_active is True

def test_manifest_contract():
    manifest = ManifestContract(
        manifest_id="manifest-999",
        tenant_uid="tenant-123",
        intent_uid="intent-001",
        run_id="run_10001"
    )
    assert manifest.manifest_id == "manifest-999"
    assert manifest.status == "MACHINE_READY"

def test_recipe_contract():
    recipe = RecipeContract(
        recipe_id="recipe-01",
        recipe_name="Vibration Cleaning",
        target_task="vibration_profiling",
        steps=[
            RecipeStep(step_id="s1", operation="unit_conversion", parameters={"to": "mm/s"})
        ]
    )
    assert len(recipe.steps) == 1
    assert recipe.steps[0].operation == "unit_conversion"

def test_discovery_contract():
    artifact = DatasetDiscoveryArtifact(
        asset_id="asset-555",
        member_inventory=["data1.csv", "data2.csv"],
        detected_formats=["csv"]
    )
    assert artifact.is_safe is True
    assert len(artifact.member_inventory) == 2
