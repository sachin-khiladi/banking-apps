#!/usr/bin/env bash
set -euo pipefail

RG_NAME="${1:-rg-bankapi-dev}"
ENV_DIR="${2:-infra/environments/dev}"
REPORTS_DIR="${3:-agents-communication/reports}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PARITY_SCRIPT="${REPO_ROOT}/scripts/terraform_parity_audit.py"

if [[ ! -f "${PARITY_SCRIPT}" ]]; then
  echo "ERROR: Missing parity script at ${PARITY_SCRIPT}" >&2
  exit 1
fi

for cmd in az terraform python3; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "ERROR: Required command '${cmd}' is not available in PATH" >&2
    exit 1
  fi
done

mkdir -p "${REPO_ROOT}/${REPORTS_DIR}"

LIVE_GROUP_JSON="${REPO_ROOT}/${REPORTS_DIR}/live-rg-bankapi-dev.group.json"
LIVE_NORMALIZED_JSON="${REPO_ROOT}/${REPORTS_DIR}/live-rg-bankapi-dev.normalized.json"
TF_NORMALIZED_JSON="${REPO_ROOT}/${REPORTS_DIR}/tf-dev-managed-resources.normalized.json"

RAW_LIVE_TMP="$(mktemp)"
RAW_TF_STATE_TMP="$(mktemp)"

cleanup() {
  rm -f "${RAW_LIVE_TMP}" "${RAW_TF_STATE_TMP}"
}
trap cleanup EXIT

echo "[1/5] Exporting resource group metadata for ${RG_NAME}"
az group show -n "${RG_NAME}" -o json > "${LIVE_GROUP_JSON}"

echo "[2/5] Exporting live resource inventory for ${RG_NAME}"
az resource list -g "${RG_NAME}" -o json > "${RAW_LIVE_TMP}"

echo "[3/5] Normalizing live resource inventory"
python3 - <<PY
import json
from pathlib import Path
raw = json.loads(Path("${RAW_LIVE_TMP}").read_text())
items = []
for resource in raw:
    items.append(
        {
            "id": resource.get("id"),
            "name": resource.get("name"),
            "type": (resource.get("type") or "").lower(),
            "location": resource.get("location"),
            "kind": resource.get("kind"),
            "managedBy": resource.get("managedBy"),
            "tags": resource.get("tags") or {},
        }
    )
items.sort(key=lambda item: (item["type"], item["name"] or ""))
Path("${LIVE_NORMALIZED_JSON}").write_text(json.dumps(items, indent=2))
print(f"live_normalized_count={len(items)}")
PY

echo "[4/5] Pulling Terraform state and normalizing managed resources"
terraform -chdir="${REPO_ROOT}/${ENV_DIR}" state pull > "${RAW_TF_STATE_TMP}"
python3 - <<PY
import json
from pathlib import Path
state = json.loads(Path("${RAW_TF_STATE_TMP}").read_text())
output = []
for resource in state.get("resources", []):
    if resource.get("mode") != "managed":
        continue
    if not (resource.get("type") or "").startswith("azurerm_"):
        continue

    module_prefix = f"{resource.get('module')}." if resource.get("module") else ""
    for instance in resource.get("instances", []):
        attributes = instance.get("attributes") or {}
        output.append(
            {
                "address": f"{module_prefix}{resource.get('type')}.{resource.get('name')}",
                "type": resource.get("type"),
                "name": attributes.get("name") or resource.get("name"),
                "id": attributes.get("id"),
                "resource_group_name": attributes.get("resource_group_name"),
                "location": attributes.get("location"),
            }
        )

output.sort(key=lambda item: (item["type"], item["name"] or item["address"] or ""))
Path("${TF_NORMALIZED_JSON}").write_text(json.dumps(output, indent=2))
print(f"tf_normalized_count={len(output)}")
PY

echo "[5/5] Running parity diff report"
python3 "${PARITY_SCRIPT}"

echo "Parity report generated at: ${REPO_ROOT}/${REPORTS_DIR}/terraform-parity-report.md"