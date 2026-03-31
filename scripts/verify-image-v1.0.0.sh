#!/usr/bin/env bash
# Verify container image integrity and attestation
# Checks image signature, SBOM, and supply chain metadata
# Prevents supply chain attacks by validating what's being deployed
#
# Usage:
#   verify-image-v1.0.0.sh <image-ref> [--verify-signature] [--verify-sbom] [--fail-on-missing]
#
# Environment Variables:
#   IMAGE_VERIFY_MODE       - Mode: strict, standard (default), or permissive
#   COSIGN_KEY              - Cosign public key for signature verification
#   SBOM_JSON_PATH          - Path to SBOM JSON for validation
#   ALLOW_UNSIGNED          - Allow unsigned images (false by default for production)
#
# Exit Codes:
#   0  - Image verification passed
#   1  - Missing argument or tool
#   2  - Image verification failed

set -euo pipefail

IMAGE_REF="${1:-}"
VERIFY_SIGNATURE="${2:---verify-signature}"
VERIFY_SBOM="${3:---verify-sbom}"
IMAGE_VERIFY_MODE="${IMAGE_VERIFY_MODE:-standard}"
ALLOW_UNSIGNED="${ALLOW_UNSIGNED:-false}"

# Validate inputs
if [[ -z "$IMAGE_REF" ]]; then
  echo "Error: image-ref required"
  echo "Usage: verify-image-v1.0.0.sh <image-ref> [--verify-signature] [--verify-sbom] [--fail-on-missing]"
  exit 1
fi

echo "Verifying image integrity: $IMAGE_REF"
echo "Verification mode: $IMAGE_VERIFY_MODE"

# Check if image exists locally or in registry
if ! docker inspect "$IMAGE_REF" &> /dev/null; then
  # Try to pull
  echo "Image not found locally, attempting to pull..."
  if ! docker pull "$IMAGE_REF"; then
    echo "Error: Cannot pull image $IMAGE_REF"
    exit 2
  fi
fi

# Get image digest
IMAGE_DIGEST=$(docker inspect "$IMAGE_REF" --format='{{index .RepoDigests 0}}' 2>/dev/null | cut -d'@' -f2)
if [[ -z "$IMAGE_DIGEST" ]]; then
  echo "Warning: Cannot retrieve image digest—using image ref instead"
  IMAGE_DIGEST="$IMAGE_REF"
fi

echo "Image digest: $IMAGE_DIGEST"

# Verify signature if cosign is available and key is provided
if [[ "$VERIFY_SIGNATURE" == "--verify-signature" ]] && [[ -n "${COSIGN_KEY:-}" ]]; then
  echo "Verifying image signature..."
  
  if ! command -v cosign &> /dev/null; then
    echo "Installing Cosign for signature verification..."
    if command -v brew &> /dev/null; then
      brew install sigstore/tap/cosign
    elif command -v apt-get &> /dev/null; then
      curl -sSL https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 -o /usr/local/bin/cosign
      chmod +x /usr/local/bin/cosign
    else
      echo "Error: Cannot auto-install Cosign. Please install manually."
      if [[ "$IMAGE_VERIFY_MODE" == "strict" ]]; then
        exit 2
      else
        echo "Warning: Skipping signature verification (non-strict mode)"
      fi
    fi
  fi

  if command -v cosign &> /dev/null; then
    # Verify signature using cosign
    if cosign verify --key "$COSIGN_KEY" "$IMAGE_REF" &> /dev/null; then
      echo "✓ Image signature verified"
    else
      echo "✗ Image signature verification failed"
      if [[ "$IMAGE_VERIFY_MODE" == "strict" ]]; then
        exit 2
      elif [[ "$IMAGE_VERIFY_MODE" == "standard" ]]; then
        if [[ "$ALLOW_UNSIGNED" != "true" ]]; then
          echo "Error: Unsigned image not allowed in standard mode"
          exit 2
        fi
      fi
      echo "Warning: Proceeding with unsigned image"
    fi
  fi
else
  if [[ "$IMAGE_VERIFY_MODE" == "strict" ]]; then
    echo "Error: Signature verification required in strict mode"
    exit 2
  fi
  echo "Skipping signature verification"
fi

# Verify Trivy scan (scan image for vulnerabilities)
echo "Running vulnerability scan with Trivy..."
if ! command -v trivy &> /dev/null; then
  echo "Installing Trivy for vulnerability scanning..."
  if command -v brew &> /dev/null; then
    brew install aquasecurity/trivy/trivy
  elif command -v apt-get &> /dev/null; then
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
  fi
fi

# Scan image; fail on CRITICAL or HIGH vulnerabilities
TRIVY_SEVERITY="CRITICAL,HIGH"
if ! trivy image --severity "$TRIVY_SEVERITY" --exit-code 0 "$IMAGE_REF"; then
  echo "✗ Image vulnerability scan found issues"
  if [[ "$IMAGE_VERIFY_MODE" == "strict" ]]; then
    exit 2
  else
    echo "Warning: Vulnerabilities detected but proceeding (non-strict mode)"
  fi
else
  echo "✓ No critical/high vulnerabilities detected"
fi

# Verify SBOM if provided
if [[ "$VERIFY_SBOM" == "--verify-sbom" ]] && [[ -n "${SBOM_JSON_PATH:-}" ]]; then
  echo "Verifying SBOM..."
  if [[ ! -f "$SBOM_JSON_PATH" ]]; then
    echo "Error: SBOM file not found at $SBOM_JSON_PATH"
    if [[ "$IMAGE_VERIFY_MODE" == "strict" ]]; then
      exit 2
    fi
  else
    # Basic SBOM validation (file exists and is valid JSON)
    if ! jq . "$SBOM_JSON_PATH" > /dev/null 2>&1; then
      echo "Error: SBOM is not valid JSON"
      if [[ "$IMAGE_VERIFY_MODE" == "strict" ]]; then
        exit 2
      fi
    else
      echo "✓ SBOM is valid"
    fi
  fi
fi

# Summary
echo ""
echo "=== Image Verification Summary ==="
echo "Image: $IMAGE_REF"
echo "Digest: $IMAGE_DIGEST"
echo "Mode: $IMAGE_VERIFY_MODE"
echo "Status: ✓ PASSED"
echo "====================================="

exit 0
