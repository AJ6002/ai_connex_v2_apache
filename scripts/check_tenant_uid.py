"""
Tenant Scope Static Analysis Script - Task 1.1.1 CI Gate.
Scans stored resource contracts in contracts/ to ensure tenant_uid field is defined.
Supports --warn-only mode for safe rollout (Golden Rule 3).
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Contracts representing stored resources that MUST carry tenant_uid
STORED_RESOURCE_CONTRACTS = {
    "DatasetContract": "contracts/dataset/dataset_contract.py",
    "ManifestContract": "contracts/manifest/manifest_contract.py",
    "AuditContract": "contracts/audit/audit_contract.py",
    "IntentContract": "contracts/intent/intent_contract.py",
    "DeploymentContract": "contracts/deployment/deployment_contract.py",
    "ModelContract": "contracts/model/model_contract.py",
    "AgentSPECContract": "contracts/agent/agent_spec_contract.py",
    "FeatureContract": "contracts/feature/feature_contract.py",
    "JobContract": "contracts/job/job_contract.py",
}


def audit_tenant_uid(strict_mode: bool = False) -> Tuple[int, List[str]]:
    repo_root = Path(__file__).resolve().parent.parent
    violations = []
    checked_count = 0

    print("[+] Auditing tenant_uid presence across stored resource contracts...")

    for class_name, rel_path in STORED_RESOURCE_CONTRACTS.items():
        file_path = repo_root / rel_path
        if not file_path.exists():
            violations.append(f"[FAIL] File missing: {rel_path}")
            continue

        content = file_path.read_text(encoding="utf-8")
        checked_count += 1

        if "tenant_uid" not in content:
            violations.append(f"[FAIL] {class_name} ({rel_path}) is missing 'tenant_uid'")
        else:
            print(f"  [OK] {class_name} ({rel_path}): tenant_uid present")

    print(f"\nAudit complete: Checked {checked_count} stored resource contracts.")

    if violations:
        print(f"\n[WARN] Found {len(violations)} violation(s):")
        for v in violations:
            print(f"  {v}")

        if strict_mode:
            print("\n[FAIL] Strict mode enabled: Failing build!")
            return 1, violations
        else:
            print("\n[WARN] Warn-only mode: Logging violations without failing build.")
            return 0, violations
    else:
        print("[PASS] Zero tenant_uid violations found across all stored resource contracts!")
        return 0, []


if __name__ == "__main__":
    strict = "--strict" in sys.argv
    exit_code, _ = audit_tenant_uid(strict_mode=strict)
    sys.exit(exit_code)
