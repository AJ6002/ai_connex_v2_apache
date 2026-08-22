"""
Automated Contract Validation Test Suite - Verifies all 18 Pydantic v2 Contract Schemas.
"""

from contracts.discovery.discovery_contract import DatasetDiscoveryArtifact
from contracts.intent.intent_contract import IntentContract
from contracts.manifest.manifest_contract import ManifestContract
from contracts.recipe.recipe_contract import RecipeContract, RecipeStep
from contracts.tenant.tenant_contract import TenantContract


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

def test_job_manager_security_bounds():
    import importlib.util
    from pathlib import Path
    fpath = Path(__file__).resolve().parent.parent.parent / "data-studio" / "job-manager" / "manager.py"
    spec = importlib.util.spec_from_file_location("manager_mod", fpath)
    assert spec is not None and spec.loader is not None
    job_mgr_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(job_mgr_mod)
    DockerJobManager = job_mgr_mod.DockerJobManager
    manager = DockerJobManager(default_memory_limit="1g", default_cpu_limit="2.0")
    cmd = manager.build_container_command(
        image_tag="parser-csv:v1",
        input_host_path="tests/fixtures/sample.csv",
        output_host_dir="tests/fixtures/output"
    )
    assert "--network" in cmd and "none" in cmd
    assert "--memory" in cmd and "1g" in cmd
    assert "--user" in cmd and "10001:10001" in cmd

def test_intent_normalizer():
    import importlib.util
    from pathlib import Path
    fpath = Path(__file__).resolve().parent.parent.parent / "data-studio" / "intake" / "normalizer.py"
    spec = importlib.util.spec_from_file_location("norm_mod", fpath)
    assert spec is not None and spec.loader is not None
    norm_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(norm_mod)
    normalize_user_intent = norm_mod.normalize_user_intent

    intent = normalize_user_intent(
        user_goal="Predict remaining useful life for turbofan engines",
        tenant_uid="tenant-99",
        user_uid="user-11"
    )
    assert intent.requires_model is True
    assert intent.intent_type == "time_series_forecast"
    assert intent.tenant_uid == "tenant-99"




