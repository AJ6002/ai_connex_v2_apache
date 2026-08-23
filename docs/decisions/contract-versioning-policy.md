# Contract Versioning & N/N-1 Compatibility Policy

> **Status:** APPROVED & ENFORCED  
> **Effective Date:** 2026-08-24  
> **Target Package:** `contracts/`  

---

## 1. Overview & SemVer Schema

Every Pydantic contract in AI-Connex must declare an explicit `schema_version` string field using Semantic Versioning (`MAJOR.MINOR.PATCH`, e.g., `"1.0.0"`).

---

## 2. N / N-1 Backward Compatibility Policy

1. **Active Horizon:** The backend runtime and API gateway must maintain dual-version tolerance for the current schema version ($N$) and the immediate prior version ($N-1$).
2. **Deprecation Grace Period:** Deprecated fields or contract shapes must remain functional for at least one minor release cycle before removal.
3. **Migration Transformers:** When receiving an $N-1$ contract shape, the system must apply a transparent up-converter to promote the payload to version $N$ before routing to downstream engines (Profiler, DAG Engine, ML Studio).

---

## 3. Breaking vs. Non-Breaking Change Rules

### Non-Breaking Changes (Increment MINOR version `x.Y.z`)
- Adding an optional field (`field: Optional[T] = None`).
- Adding a new enum member to an existing string enum.
- Adding a new optional metadata field with a sensible default.
- Adding new documentation or validation descriptions.

### Breaking Changes (Increment MAJOR version `X.0.0`)
- Removing an existing field from a contract.
- Renaming a field (e.g. `asset_name` → `name`).
- Changing a field's data type (e.g., `int` → `list[int]`).
- Changing an optional field into a required field (`default=...` → `...`).
- Removing an enum member or changing enum string values.

---

## 4. CI/CD Enforcement & Verification Rules

1. **Required Schema Version:** All Pydantic models in `contracts/` must require `schema_version` during instantiation.
2. **Missing Field Rejection:** Any payload missing `schema_version` will fail Pydantic validation with a `ValidationError`.
3. **Automated Unit Tests:** `tests/contracts/test_contracts.py` includes validation tests verifying missing-version rejection and version-presence acceptance across all 19 contract models.
