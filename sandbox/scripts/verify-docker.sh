#!/usr/bin/env bash
# Sandbox Docker & Buildx Environment Verification Script
set -euo pipefail

echo "=== Level 4 Sandbox: Docker Environment Audit ==="

# 1. Check Docker Engine
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Docker Engine is NOT installed or not in PATH."
    exit 1
fi
echo "✅ Docker Engine: $(docker --version)"

# 2. Check Buildx
if ! docker buildx version > /dev/null 2>&1; then
    echo "❌ Docker Buildx is NOT installed."
    exit 1
fi
echo "✅ Docker Buildx: $(docker buildx version | head -n1)"

# 3. Check BuildKit environment
export DOCKER_BUILDKIT=1

# 4. Verify support for security flags using alpine dry-run container
echo "Verifying runtime security flags (--network none, --user, --memory, --cpus, --read-only)..."

docker run --rm \
    --network none \
    --user 10001:10001 \
    --memory 128m \
    --cpus 0.5 \
    --read-only \
    --tmpfs /tmp \
    alpine:latest \
    id > /dev/null 2>&1

echo "✅ Docker Security Flags (--network none, --user 10001:10001, --memory, --cpus, --read-only): VERIFIED"
echo "=== Docker Verification COMPLETE ==="
