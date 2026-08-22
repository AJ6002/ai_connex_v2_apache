#!/usr/bin/env bash
# Sandbox Security Toolchain Installer (Trivy, Syft, Cosign)
set -euo pipefail

echo "=== Level 4 Security Toolchain Audit & Setup ==="

# Install Trivy
if ! command -v trivy &> /dev/null; then
    echo "Installing Trivy container scanner..."
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.50.0
else
    echo "✅ Trivy installed: $(trivy --version | head -n1)"
fi

# Install Syft
if ! command -v syft &> /dev/null; then
    echo "Installing Syft SBOM generator..."
    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin v1.0.0
else
    echo "✅ Syft installed: $(syft --version | head -n1)"
fi

# Install Cosign
if ! command -v cosign &> /dev/null; then
    echo "Installing Cosign container signer..."
    curl -O -L https://github.com/sigstore/cosign/releases/download/v2.2.3/cosign-linux-amd64
    chmod +x cosign-linux-amd64
    mv cosign-linux-amd64 /usr/local/bin/cosign
else
    echo "✅ Cosign installed: $(cosign version | head -n1)"
fi

echo "=== Security Toolchain Verification COMPLETE ==="
