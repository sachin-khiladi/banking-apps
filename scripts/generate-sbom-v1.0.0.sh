#!/usr/bin/env bash
# Generate Software Bill of Materials (SBOM) for container image
# SBOM provides transparency on image contents and dependencies
# Supports: dockerfile, image layers, installed packages
#
# Usage:
#   generate-sbom-v1.0.0.sh <image-ref> <output-json>
#
# Environment Variables:
#   SBOM_FORMAT      - Output format: spdx-json (default), cyclonedx-json, or syft-json
#   SBOM_TOOL        - Tool to use: syft (default), trivy, or manual
#
# Exit Codes:
#   0  - SBOM generated successfully
#   1  - Missing arguments or tool not available
#   2  - SBOM generation failed

set -euo pipefail

IMAGE_REF="${1:-}"
OUTPUT_JSON="${2:-sbom.json}"
SBOM_FORMAT="${SBOM_FORMAT:-spdx-json}"
SBOM_TOOL="${SBOM_TOOL:-syft}"

# Validate inputs
if [[ -z "$IMAGE_REF" ]]; then
  echo "Error: image-ref required"
  echo "Usage: generate-sbom-v1.0.0.sh <image-ref> [output-json]"
  exit 1
fi

echo "Generating SBOM for image: $IMAGE_REF"
echo "Output format: $SBOM_FORMAT"
echo "Output file: $OUTPUT_JSON"

# Ensure Syft is installed (prefer over Trivy for SBOM, more comprehensive)
if ! command -v syft &> /dev/null; then
  echo "Installing Syft for SBOM generation..."
  if command -v brew &> /dev/null; then
    brew install anchore/syft/syft
  elif command -v apt-get &> /dev/null; then
    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
  else
    echo "Error: Cannot auto-install Syft. Please install manually: https://github.com/anchore/syft"
    exit 1
  fi
fi

# Generate SBOM using Syft
echo "Generating $SBOM_FORMAT SBOM using syft..."
case "$SBOM_FORMAT" in
  spdx-json)
    syft "$IMAGE_REF" --output=spdxjson > "$OUTPUT_JSON" || {
      echo "Error: SBOM generation failed"
      exit 2
    }
    ;;
  cyclonedx-json)
    syft "$IMAGE_REF" --output=cyclonedxjson > "$OUTPUT_JSON" || {
      echo "Error: SBOM generation failed"
      exit 2
    }
    ;;
  syft-json)
    syft "$IMAGE_REF" --output=json > "$OUTPUT_JSON" || {
      echo "Error: SBOM generation failed"
      exit 2
    }
    ;;
  *)
    echo "Error: Unsupported SBOM format: $SBOM_FORMAT"
    echo "Valid formats: spdx-json, cyclonedx-json, syft-json"
    exit 1
    ;;
esac

# Verify SBOM was created
if [[ ! -f "$OUTPUT_JSON" ]]; then
  echo "Error: SBOM file not created at $OUTPUT_JSON"
  exit 2
fi

# Report SBOM stats
if command -v jq &> /dev/null; then
  PACKAGE_COUNT=$(jq '.artifacts | length // .components | length // 0' "$OUTPUT_JSON")
  echo "✓ SBOM generated successfully"
  echo "  Packages/Components: $PACKAGE_COUNT"
else
  echo "✓ SBOM generated successfully"
  echo "  File: $OUTPUT_JSON"
fi

exit 0
