#!/usr/bin/env bash
# Sandbox Security Toolchain Installer (Trivy, Syft, Cosign)
set -euo pipefail

echo "=== Level 4 Security Toolchain Audit & Setup ==="

# 1. Verify / Install Trivy
if ! command -v trivy &> /dev/null; then
    echo "Installing Trivy container scanner..."
    curl -sSfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.50.0 || {
        echo "Fallback: Installing Trivy via apt..."
        apt-get update -qq && apt-get install -y -qq trivy || true
    }
fi
if command -v trivy &> /dev/null; then
    echo "[OK] Trivy verified: $(trivy --version | head -n1)"
else
    echo "[WARN] Trivy not found in PATH"
fi

# 2. Verify / Install Syft
if ! command -v syft &> /dev/null; then
    echo "Installing Syft SBOM generator..."
    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin v1.0.0 || true
fi
if command -v syft &> /dev/null; then
    echo "[OK] Syft verified: $(syft --version | head -n1)"
else
    echo "[WARN] Syft not found in PATH"
fi

# 3. Verify / Install Cosign
if ! command -v cosign &> /dev/null; then
    echo "Installing Cosign container signer..."
    curl -sSfL -o /usr/local/bin/cosign https://github.com/sigstore/cosign/releases/download/v2.2.3/cosign-linux-amd64 || true
    chmod +x /usr/local/bin/cosign || true
fi
if command -v cosign &> /dev/null; then
    echo "[OK] Cosign verified: $(cosign version 2>&1 | head -n1)"
else
    echo "[WARN] Cosign not found in PATH"
fi

echo "=== Security Toolchain Verification COMPLETE ==="
