#!/usr/bin/env bash
set -euo pipefail

ACR_NAME_DEFAULT="acrbankapidevc8775a"
ACR_LOGIN_SERVER_DEFAULT="acrbankapidevc8775a.azurecr.io"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IMAGE_NAME="bank-api"
IMAGE_TAG="latest"
PLATFORMS="linux/amd64,linux/arm64"
DOCKERFILE_PATH="$SCRIPT_DIR/../Dockerfile"
BUILD_CONTEXT="$SCRIPT_DIR/.."

ACR_NAME="${ACR_NAME:-$ACR_NAME_DEFAULT}"
ACR_LOGIN_SERVER="${ACR_LOGIN_SERVER:-$ACR_LOGIN_SERVER_DEFAULT}"

usage() {
  cat <<'EOF'
Usage:
  scripts/build_and_push_acr.sh [options]

Builds a multi-platform Docker image using docker buildx and pushes it to Azure Container Registry.

Options:
  --image <name>        Image name in ACR (default: bank-api)
  --tag <tag>           Image tag (default: latest)
  --platforms <list>    Comma-separated platforms (default: linux/amd64,linux/arm64)
  --dockerfile <path>   Dockerfile path (default: ../Dockerfile)
  --context <path>      Build context (default: ..)
  -h, --help            Show help

Environment overrides:
  ACR_NAME, ACR_LOGIN_SERVER

Examples:
  scripts/build_and_push_acr.sh
  scripts/build_and_push_acr.sh --tag v1
  scripts/build_and_push_acr.sh --platforms linux/amd64

Outputs:
  Pushes:
    $ACR_LOGIN_SERVER/<image>:<tag>
EOF
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "ERROR: Required command not found: $cmd" >&2
    exit 1
  }
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      IMAGE_NAME="$2"
      shift 2
      ;;
    --tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    --platforms)
      PLATFORMS="$2"
      shift 2
      ;;
    --dockerfile)
      DOCKERFILE_PATH="$2"
      shift 2
      ;;
    --context)
      BUILD_CONTEXT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

require_cmd az
require_cmd docker

if ! docker buildx version >/dev/null 2>&1; then
  echo "ERROR: docker buildx is not available. Update Docker Desktop or install buildx." >&2
  exit 1
fi

echo "ACR_NAME=$ACR_NAME"
echo "ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER"
echo "IMAGE=$IMAGE_NAME:$IMAGE_TAG"
echo "PLATFORMS=$PLATFORMS"
echo "DOCKERFILE=$DOCKERFILE_PATH"
echo "CONTEXT=$BUILD_CONTEXT"

echo "Logging into ACR via Azure CLI..."
az acr login --name "$ACR_NAME" >/dev/null

# Ensure a buildx builder exists and is selected.
if ! docker buildx inspect >/dev/null 2>&1; then
  docker buildx create --use --name "buildx-${ACR_NAME}" >/dev/null
fi

FULL_TAG="$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"

echo "Building and pushing: $FULL_TAG"
docker buildx build \
  --platform "$PLATFORMS" \
  --file "$DOCKERFILE_PATH" \
  --tag "$FULL_TAG" \
  --push \
  "$BUILD_CONTEXT"

echo "Done. Pushed: $FULL_TAG"
