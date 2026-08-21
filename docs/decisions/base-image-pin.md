# ADR 001: Pinned Base Container Image Digest

**Status:** Accepted  
**Date:** August 21, 2026  
**Deciders:** Core Engineering Team  
**Scope:** `Dockerfile`, `sandbox/parser-images/*.Dockerfile`  

---

## Context
Floating base image tags such as `python:3.11-slim` introduce non-deterministic builds across different developer machines and CI/CD runners. Upstream changes in Debian or Python base packages can introduce unexpected vulnerability regressions, broken C libraries, or version drift.

## Decision
All Dockerfiles across the AI-Connex repository shall pin the base image to an explicit SHA-256 digest:

```dockerfile
FROM python:3.11-slim@sha256:9c900dea9e8fb7e16277c179b555cc72d29a352dbc33cff48ad5a0412fd5bfc7
```

## Consequences
- **Build Reproducibility**: 100% bit-for-bit identical container layer baselines on local machines and GitHub Actions CI.
- **Security Compliance**: Trivy vulnerability scans produce deterministic results.
- **Update Process**: Updating the base image requires explicit SHA-256 digest updates reviewed via Pull Request.
