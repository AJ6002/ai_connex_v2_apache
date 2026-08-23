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
        schema_version="1.0.0",
        user_uid="user-456",
        goal="Predict turbofan RUL",
        intent_type="time_series_forecast"
    )
    assert contract.intent_uid == "intent-001"
    assert contract.schema_version == "1.0.0"
    assert contract.autonomy_requested == "HITL"

def test_tenant_contract():
    contract = TenantContract(
        tenant_id="tenant-123",
        schema_version="1.0.0",
        tenant_name="Industrial Energy Corp",
        user_id="user-456"
    )
    assert contract.tenant_id == "tenant-123"
    assert contract.schema_version == "1.0.0"
    assert contract.is_active is True

def test_manifest_contract():
    manifest = ManifestContract(
        manifest_id="manifest-999",
        tenant_uid="tenant-123",
        schema_version="1.0.0",
        intent_uid="intent-001",
        run_id="run_10001"
    )
    assert manifest.manifest_id == "manifest-999"
    assert manifest.schema_version == "1.0.0"
    assert manifest.status == "MACHINE_READY"

def test_recipe_contract():
    recipe = RecipeContract(
        recipe_id="recipe-01",
        schema_version="1.0.0",
        recipe_name="Vibration Cleaning",
        target_task="vibration_profiling",
        steps=[
            RecipeStep(step_id="s1", operation="unit_conversion", parameters={"to": "mm/s"})
        ]
    )
    assert len(recipe.steps) == 1
    assert recipe.schema_version == "1.0.0"
    assert recipe.steps[0].operation == "unit_conversion"

def test_discovery_contract():
    artifact = DatasetDiscoveryArtifact(
        asset_id="asset-555",
        schema_version="1.0.0",
        member_inventory=["data1.csv", "data2.csv"],
        detected_formats=["csv"]
    )
    assert artifact.is_safe is True
    assert artifact.schema_version == "1.0.0"
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


def test_job_contract():
    from contracts.job.job_contract import JobContract, JobStageContract, JobStageStatus, JobStatus
    job = JobContract(
        job_id="JOB-8294",
        tenant_uid="tenant-123",
        schema_version="1.0.0",
        intent_uid="intent-001",
        status=JobStatus.RUNNING,
        stages=[
            JobStageContract(key="INTAKE", label="Intake", status=JobStageStatus.DONE),
            JobStageContract(key="PROFILER", label="Profiler", status=JobStageStatus.RUNNING, progress_pct=64.0)
        ]
    )
    assert job.job_id == "JOB-8294"
    assert job.tenant_uid == "tenant-123"
    assert job.schema_version == "1.0.0"
    assert job.status == JobStatus.RUNNING
    assert len(job.stages) == 2
    assert job.stages[1].status == JobStageStatus.RUNNING


def test_model_contract():
    from contracts.model.model_contract import ModelContract
    model = ModelContract(
        model_id="model-001",
        tenant_uid="tenant-123",
        schema_version="1.0.0",
        manifest_id="manifest-999",
        algorithm_name="XGBoost",
        task_type="TimeSeries"
    )
    assert model.model_id == "model-001"
    assert model.tenant_uid == "tenant-123"
    assert model.schema_version == "1.0.0"


def test_agent_spec_contract():
    from contracts.agent.agent_spec_contract import AgentSPECContract
    agent = AgentSPECContract(
        agent_id="agent-001",
        tenant_uid="tenant-123",
        schema_version="1.0.0",
        agent_name="Jane"
    )
    assert agent.agent_id == "agent-001"
    assert agent.tenant_uid == "tenant-123"
    assert agent.schema_version == "1.0.0"


def test_feature_contract():
    from contracts.feature.feature_contract import FeatureContract
    feat = FeatureContract(
        feature_set_id="feat-001",
        tenant_uid="tenant-123",
        schema_version="1.0.0",
        manifest_id="manifest-999"
    )
    assert feat.feature_set_id == "feat-001"
    assert feat.tenant_uid == "tenant-123"
    assert feat.schema_version == "1.0.0"


def test_profile_summary_contract():
    from contracts.profile.profile_contract import ColumnSummaryContract, ProfileSummaryContract
    summary = ProfileSummaryContract(
        manifest_id="manifest-100",
        schema_version="1.0.0",
        dataset_ref="ds-001",
        dataset_name="transactions_main",
        row_count=24000,
        column_count=12,
        columns=[
            ColumnSummaryContract(name="timestamp", dtype="datetime", null_ratio=0.0, distinct_count=24000),
            ColumnSummaryContract(name="temp_c", dtype="float", null_ratio=0.01, distinct_count=8123)
        ],
        recommended_dag_id="DAG_906",
        algorithm_family="Time-Series Regression",
        narrative="Time-indexed multi-sensor telemetry suitable for RUL profiling."
    )
    assert summary.dataset_name == "transactions_main"
    assert summary.schema_version == "1.0.0"
    assert len(summary.columns) == 2
    assert summary.columns[0].dtype == "datetime"


def test_contract_schema_version_coverage():
    """Verify Task 1.1.2 requirement: All contract models instantiate with schema_version present."""
    from datetime import datetime
    from contracts.agent.agent_spec_contract import AgentSPECContract
    from contracts.audit.audit_contract import AuditContract
    from contracts.dag.dag_contract import DAGContract
    from contracts.dataset.dataset_contract import DatasetContract
    from contracts.deployment.deployment_contract import DeploymentContract
    from contracts.discovery.discovery_contract import DatasetDiscoveryArtifact
    from contracts.feature.feature_contract import FeatureContract
    from contracts.intent.intent_contract import IntentContract
    from contracts.job.job_contract import JobContract
    from contracts.manifest.manifest_contract import ManifestContract
    from contracts.model.model_contract import ModelContract
    from contracts.prepare.prepare_contract import PrepareContract
    from contracts.profile.profile_contract import ProfileContract
    from contracts.recipe.recipe_contract import RecipeContract
    from contracts.sandbox.result_manifest_contract import ParserResultManifest
    from contracts.segmentation.segmentation_contract import CandidateRegion, SegmentationProposal
    from contracts.telemetry.telemetry_contract import TelemetryContract
    from contracts.tenant.tenant_contract import TenantContract
    from contracts.tool.tool_contract import ToolContract

    contracts = [
        AgentSPECContract(agent_id="a1", tenant_uid="t1", agent_name="Jane", schema_version="1.2.0"),
        AuditContract(audit_id="au1", tenant_uid="t1", user_uid="u1", action="A", resource_type="R", resource_id="r1", schema_version="1.1.0"),
        DAGContract(dag_id="d1", dag_name="N", description="D", output_target="T", schema_version="1.0.0"),
        DatasetContract(asset_id="ds1", tenant_uid="t1", asset_name="N", storage_uri="s3://", format="csv", size_bytes=10, sha256_hash="h", schema_version="2.0.0"),
        DeploymentContract(deployment_id="dep1", model_id="m1", tenant_uid="t1", endpoint_url="http://", schema_version="1.0.0"),
        DatasetDiscoveryArtifact(asset_id="asset1", schema_version="1.0.0"),
        FeatureContract(feature_set_id="f1", tenant_uid="t1", manifest_id="m1", schema_version="1.0.0"),
        IntentContract(intent_uid="i1", tenant_uid="t1", user_uid="u1", goal="G", intent_type="T", schema_version="1.0.0"),
        JobContract(job_id="j1", tenant_uid="t1", intent_uid="i1", schema_version="1.0.0"),
        ManifestContract(manifest_id="m1", tenant_uid="t1", intent_uid="i1", run_id="r1", schema_version="1.0.0"),
        ModelContract(model_id="mod1", tenant_uid="t1", manifest_id="m1", algorithm_name="XGB", task_type="T", schema_version="1.0.0"),
        PrepareContract(manifest_id="m1", schema_version="1.0.0"),
        ProfileContract(manifest_id="m1", row_count=10, column_count=2, schema_version="1.0.0"),
        RecipeContract(recipe_id="r1", recipe_name="N", target_task="T", schema_version="1.0.0"),
        ParserResultManifest(job_id="j1", image_name="img", image_digest="d", input_file="f", input_hash="h", output_parquet="p", output_hash="oh", row_count=5, started_at=datetime.utcnow(), completed_at=datetime.utcnow(), schema_version="1.0.0"),
        CandidateRegion(source_file="f", row_start=0, row_end=1, col_start=0, col_end=1, confidence=0.9, proposed_table_name="t", schema_version="1.0.0"),
        SegmentationProposal(asset_id="ast1", schema_version="1.0.0"),
        TelemetryContract(sensor_id="s1", asset_id="ast1", value=42.0, unit="C", schema_version="1.0.0"),
        TenantContract(tenant_id="t1", tenant_name="N", user_id="u1", schema_version="1.0.0"),
        ToolContract(tool_id="tool1", capability_name="C", schema_version="1.0.0"),
    ]

    for c in contracts:
        assert hasattr(c, "schema_version")
        assert len(c.schema_version) > 0


def test_missing_required_field_rejection():
    """Task 1.1.3: Verify missing required field rejection across contracts."""
    import pytest
    from pydantic import ValidationError
    from contracts.dataset.dataset_contract import DatasetContract
    from contracts.model.model_contract import ModelContract
    from contracts.intent.intent_contract import IntentContract

    # Missing storage_uri
    with pytest.raises(ValidationError):
        DatasetContract(asset_id="ds1", tenant_uid="t1", asset_name="N", format="csv", size_bytes=10, sha256_hash="h")

    # Missing algorithm_name
    with pytest.raises(ValidationError):
        ModelContract(model_id="m1", tenant_uid="t1", manifest_id="man1", task_type="TimeSeries")

    # Missing goal
    with pytest.raises(ValidationError):
        IntentContract(intent_uid="i1", tenant_uid="t1", user_uid="u1", intent_type="upload")


def test_wrong_type_rejection():
    """Task 1.1.3: Verify wrong type field rejection across contracts."""
    import pytest
    from pydantic import ValidationError
    from contracts.dataset.dataset_contract import DatasetContract
    from contracts.telemetry.telemetry_contract import TelemetryContract

    # Wrong type for size_bytes (dict instead of int)
    with pytest.raises(ValidationError):
        DatasetContract(
            asset_id="ds1", tenant_uid="t1", asset_name="N", storage_uri="s3://",
            format="csv", size_bytes={"invalid": "type"}, sha256_hash="h"
        )

    # Wrong type for value (string instead of float)
    with pytest.raises(ValidationError):
        TelemetryContract(sensor_id="s1", asset_id="a1", value="invalid_float_string", unit="C")


def test_roundtrip_serialization_all_contracts():
    """Task 1.1.3: Verify round-trip JSON serialization and deserialization across all contracts."""
    from datetime import datetime
    from contracts.agent.agent_spec_contract import AgentSPECContract
    from contracts.audit.audit_contract import AuditContract
    from contracts.dag.dag_contract import DAGContract
    from contracts.dataset.dataset_contract import DatasetContract
    from contracts.deployment.deployment_contract import DeploymentContract
    from contracts.discovery.discovery_contract import DatasetDiscoveryArtifact
    from contracts.feature.feature_contract import FeatureContract
    from contracts.intent.intent_contract import IntentContract
    from contracts.job.job_contract import JobContract
    from contracts.manifest.manifest_contract import ManifestContract
    from contracts.model.model_contract import ModelContract
    from contracts.prepare.prepare_contract import PrepareContract
    from contracts.profile.profile_contract import ProfileContract
    from contracts.recipe.recipe_contract import RecipeContract
    from contracts.sandbox.result_manifest_contract import ParserResultManifest
    from contracts.segmentation.segmentation_contract import CandidateRegion, SegmentationProposal
    from contracts.telemetry.telemetry_contract import TelemetryContract
    from contracts.tenant.tenant_contract import TenantContract
    from contracts.tool.tool_contract import ToolContract

    now = datetime.utcnow()
    instances = [
        (AgentSPECContract, AgentSPECContract(agent_id="a1", tenant_uid="t1", agent_name="Jane", schema_version="1.0.0")),
        (AuditContract, AuditContract(audit_id="au1", tenant_uid="t1", user_uid="u1", action="A", resource_type="R", resource_id="r1", timestamp=now)),
        (DAGContract, DAGContract(dag_id="d1", dag_name="N", description="D", output_target="T")),
        (DatasetContract, DatasetContract(asset_id="ds1", tenant_uid="t1", asset_name="N", storage_uri="s3://", format="csv", size_bytes=10, sha256_hash="h", created_at=now)),
        (DeploymentContract, DeploymentContract(deployment_id="dep1", model_id="m1", tenant_uid="t1", endpoint_url="http://")),
        (DatasetDiscoveryArtifact, DatasetDiscoveryArtifact(asset_id="asset1")),
        (FeatureContract, FeatureContract(feature_set_id="f1", tenant_uid="t1", manifest_id="m1")),
        (IntentContract, IntentContract(intent_uid="i1", tenant_uid="t1", user_uid="u1", goal="G", intent_type="T")),
        (JobContract, JobContract(job_id="j1", tenant_uid="t1", intent_uid="i1", created_at=now, updated_at=now)),
        (ManifestContract, ManifestContract(manifest_id="m1", tenant_uid="t1", intent_uid="i1", run_id="r1", created_at=now, updated_at=now)),
        (ModelContract, ModelContract(model_id="mod1", tenant_uid="t1", manifest_id="m1", algorithm_name="XGB", task_type="T", created_at=now)),
        (PrepareContract, PrepareContract(manifest_id="m1")),
        (ProfileContract, ProfileContract(manifest_id="m1", row_count=10, column_count=2)),
        (RecipeContract, RecipeContract(recipe_id="r1", recipe_name="N", target_task="T")),
        (ParserResultManifest, ParserResultManifest(job_id="j1", image_name="img", image_digest="d", input_file="f", input_hash="h", output_parquet="p", output_hash="oh", row_count=5, started_at=now, completed_at=now)),
        (CandidateRegion, CandidateRegion(source_file="f", row_start=0, row_end=1, col_start=0, col_end=1, confidence=0.9, proposed_table_name="t")),
        (SegmentationProposal, SegmentationProposal(asset_id="ast1", created_at=now)),
        (TelemetryContract, TelemetryContract(sensor_id="s1", asset_id="ast1", value=42.0, unit="C", timestamp=now)),
        (TenantContract, TenantContract(tenant_id="t1", tenant_name="N", user_id="u1")),
        (ToolContract, ToolContract(tool_id="tool1", capability_name="C")),
    ]

    for model_cls, original in instances:
        json_data = original.model_dump_json()
        deserialized = model_cls.model_validate_json(json_data)
        assert deserialized.schema_version == original.schema_version







