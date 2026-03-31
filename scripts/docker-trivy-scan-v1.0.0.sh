#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:-}"
SEVERITY="${2:-CRITICAL,HIGH}"

if [[ -z "$IMAGE_REF" ]]; then
  echo "docker image reference is required"
  exit 1
fi

if ! command -v trivy >/dev/null 2>&1; then
  echo "trivy not found; installing"
  if command -v brew >/dev/null 2>&1; then
    brew install trivy
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y wget apt-transport-https gnupg lsb-release
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
    echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/trivy.list
    sudo apt-get update
    sudo apt-get install -y trivy
  else
    echo "unable to install trivy automatically"
    exit 1
  fi
fi

trivy image --severity "$SEVERITY" --exit-code 1 "$IMAGE_REF"
