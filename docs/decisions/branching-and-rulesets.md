# Branching Strategy, Rulesets & GitHub Environments Guide

**Repository:** `ai_connex_v2_apache`  
**Classification:** Enterprise DevOps & Source Control Policy  

---

## 1. Branching Strategy

| Branch | Role | Merge Requirements |
|---|---|---|
| `main` | Production release branch | Requires PR + ≥1 approval + passing CI |
| `develop` | Integration branch | Requires PR + passing CI |
| `feature/*` | Feature development branches | Branch off `develop`, merged via PR |

---

## 2. GitHub Rulesets on `main`

Configure in GitHub Repository Settings -> **Rulesets** -> **New branch ruleset**:

* **Target Branch**: `refs/heads/main`
* **Rules Enforced**:
  1. `Block direct pushes` (Restricts commits pushed directly to `main`).
  2. `Block force pushes` (`--force` / `--force-with-lease` disabled).
  3. `Require Pull Request before merging`:
     - Minimum required approvals: `1`
     - Dismiss stale pull request approvals when new commits are pushed.
  4. `Require status checks to pass before merging`:
     - `Lint, Typecheck & Contract Tests`
     - `Frontend Shell Build & Verification`
     - `Container Build Verification`

---

## 3. GitHub Container Registry (GHCR) Configuration

Configured directly in `.github/workflows/ci.yml`:

```yaml
publish-ghcr-images:
  permissions:
    contents: read
    packages: write
```

* **Authentication**: Automatic login via `secrets.GITHUB_TOKEN`.
* **Image Registry Tag**: `ghcr.io/aj6002/ai_connex_v2_apache/aiconnex-base:latest` and `:${{ github.sha }}`.

---

## 4. GitHub Environments & Deployment Gates

Configure under GitHub Settings -> **Environments**:

1. **`development`**: Continuous integration target for `develop` branch.
2. **`staging`**: Automated staging deployment target for `main` branch.
3. **`production`**: Production deployment target requiring **Required reviewers** (manual approval gate).
