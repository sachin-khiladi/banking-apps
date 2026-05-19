#!/usr/bin/env bash
set -euo pipefail

# Manual prerequisite bootstrap for Terraform pipeline identity.
# Run this with a privileged operator identity (Owner or User Access Administrator)
# before running infra apply workflows.

usage() {
  cat <<'EOF'
Usage:
  scripts/bootstrap_pipeline_rbac.sh \
    --client-id <service-principal-client-id> \
    [--object-id <service-principal-object-id>] \
    [--subscription-id <subscription-id>] \
    [--resource-group <resource-group-name>] \
    [--acr-name <acr-name>] \
    [--keyvault-name <keyvault-name>] \
    [--appconfig-name <appconfig-name>]

Description:
  Idempotently assigns required roles to the Terraform/GitHub federated deployer identity.
  Always grants subscription-scope Contributor + ABAC-constrained User Access Administrator.
  Optionally grants resource-scope roles for existing resources:
    - ACR: AcrPush
    - Key Vault: Key Vault Administrator
    - App Configuration: App Configuration Data Owner

Examples:
  scripts/bootstrap_pipeline_rbac.sh \
    --client-id 05baf6a1-cae6-442a-94d6-f0d1f64b61f4 \
    --object-id cd7ca1e6-67f4-4120-b3a2-615de398cc6a

  scripts/bootstrap_pipeline_rbac.sh \
    --client-id 05baf6a1-cae6-442a-94d6-f0d1f64b61f4 \
    --object-id cd7ca1e6-67f4-4120-b3a2-615de398cc6a \
    --resource-group rg-bankapi-dev \
    --acr-name acrbankapidevc8775a \
    --keyvault-name kv-bankapi-dev-c8775a \
    --appconfig-name appcs-bankapi-dev
EOF
}

PIPELINE_CLIENT_ID=""
PIPELINE_OBJECT_ID=""
SUBSCRIPTION_ID=""
RESOURCE_GROUP=""
ACR_NAME=""
KEYVAULT_NAME=""
APPCONFIG_NAME=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --client-id)
      PIPELINE_CLIENT_ID="$2"
      shift 2
      ;;
    --object-id)
      PIPELINE_OBJECT_ID="$2"
      shift 2
      ;;
    --subscription-id)
      SUBSCRIPTION_ID="$2"
      shift 2
      ;;
    --resource-group)
      RESOURCE_GROUP="$2"
      shift 2
      ;;
    --acr-name)
      ACR_NAME="$2"
      shift 2
      ;;
    --keyvault-name)
      KEYVAULT_NAME="$2"
      shift 2
      ;;
    --appconfig-name)
      APPCONFIG_NAME="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${PIPELINE_CLIENT_ID}" ]]; then
  echo "--client-id is required." >&2
  usage
  exit 1
fi

readonly CONTRIBUTOR_ROLE_ID="b24988ac-6180-42a0-ab88-20f7382dd24c"
readonly UAA_ROLE_ID="18d7d88d-d35e-4fb5-a5c3-7773c20a72d9"
readonly ACR_PULL_ROLE_ID="7f951dda-4ed3-4680-a7ca-43fe172d538d"
readonly ACR_PUSH_ROLE_ID="8311e382-0749-4cb8-b61a-304f252e45ec"
readonly KV_ADMIN_ROLE_ID="00482a5a-887f-4fb3-b363-3b7fe8e74483"
readonly KV_SECRETS_USER_ROLE_ID="4633458b-17de-408a-b874-0445c86b69e6"
readonly APPCONFIG_OWNER_ROLE_ID="5ae67dd6-50cb-40e7-96ff-dc2bfa4b606b"
readonly APPCONFIG_READER_ROLE_ID="516239f1-63e1-4d78-a4de-a74fb236a071"

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI is required but was not found in PATH." >&2
  exit 1
fi

if [[ -z "${SUBSCRIPTION_ID}" ]]; then
  SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
fi
SUBSCRIPTION_SCOPE="/subscriptions/${SUBSCRIPTION_ID}"

readonly UAA_ABAC_CONDITION="(
  (
    !(ActionMatches{'Microsoft.Authorization/roleAssignments/write'})
  )
  OR
  (
    @Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {
      ${UAA_ROLE_ID},
      ${CONTRIBUTOR_ROLE_ID},
      ${ACR_PULL_ROLE_ID},
      ${ACR_PUSH_ROLE_ID},
      ${KV_ADMIN_ROLE_ID},
      ${KV_SECRETS_USER_ROLE_ID},
      ${APPCONFIG_OWNER_ROLE_ID},
      ${APPCONFIG_READER_ROLE_ID}
    }
  )
)"

echo "Using subscription: ${SUBSCRIPTION_ID}"
echo "Target principal client id: ${PIPELINE_CLIENT_ID}"
resolved_oid="$(az ad sp show --id "${PIPELINE_CLIENT_ID}" --query id -o tsv)"
if [[ -z "${PIPELINE_OBJECT_ID}" ]]; then
  PIPELINE_OBJECT_ID="${resolved_oid}"
  echo "Resolved principal object id from client id: ${PIPELINE_OBJECT_ID}"
elif [[ "${resolved_oid}" != "${PIPELINE_OBJECT_ID}" ]]; then
  echo "WARNING: --client-id resolves to object id ${resolved_oid}, but --object-id was ${PIPELINE_OBJECT_ID}." >&2
  echo "WARNING: Continuing with resolved service principal object id: ${resolved_oid}" >&2
  PIPELINE_OBJECT_ID="${resolved_oid}"
fi
echo "Target principal object id: ${PIPELINE_OBJECT_ID}"
echo

echo "Current subscription-scope assignments for target principal:"
az role assignment list \
  --assignee-object-id "${PIPELINE_OBJECT_ID}" \
  --scope "${SUBSCRIPTION_SCOPE}" \
  --query "[].{role:roleDefinitionName,scope:scope,condition:condition}" \
  -o table
echo

assignment_exists() {
  local role_name="$1"
  local query="[?roleDefinitionName=='${role_name}' && scope=='${SUBSCRIPTION_SCOPE}'] | length(@)"
  local count
  count="$(az role assignment list \
    --assignee-object-id "${PIPELINE_OBJECT_ID}" \
    --scope "${SUBSCRIPTION_SCOPE}" \
    --query "${query}" \
    -o tsv)"
  [[ "${count:-0}" != "0" ]]
}

if assignment_exists "Contributor"; then
  echo "Contributor already assigned at subscription scope; skipping create."
else
  echo "Assigning Contributor at subscription scope..."
  az role assignment create \
    --assignee-object-id "${PIPELINE_OBJECT_ID}" \
    --assignee-principal-type ServicePrincipal \
    --role "Contributor" \
    --scope "${SUBSCRIPTION_SCOPE}" \
    --only-show-errors \
    1>/dev/null
  echo "Contributor assignment created."
fi

if assignment_exists "User Access Administrator"; then
  echo "User Access Administrator already assigned at subscription scope; skipping create."
  echo "If the existing assignment is unconditioned, remove it manually and rerun to apply ABAC narrowing."
else
  echo "Assigning User Access Administrator with ABAC condition at subscription scope..."
  az role assignment create \
    --assignee-object-id "${PIPELINE_OBJECT_ID}" \
    --assignee-principal-type ServicePrincipal \
    --role "User Access Administrator" \
    --scope "${SUBSCRIPTION_SCOPE}" \
    --condition-version "2.0" \
    --condition "${UAA_ABAC_CONDITION}" \
    --only-show-errors \
    1>/dev/null
  echo "User Access Administrator assignment created with ABAC condition."
fi

assignment_exists_for_scope() {
  local role_name="$1"
  local scope="$2"
  local query="[?roleDefinitionName=='${role_name}' && scope=='${scope}'] | length(@)"
  local count
  count="$(az role assignment list \
    --assignee-object-id "${PIPELINE_OBJECT_ID}" \
    --scope "${scope}" \
    --query "${query}" \
    -o tsv)"
  [[ "${count:-0}" != "0" ]]
}

ensure_role_assignment() {
  local role_name="$1"
  local scope="$2"

  if assignment_exists_for_scope "${role_name}" "${scope}"; then
    echo "${role_name} already assigned at ${scope}; skipping create."
    return
  fi

  echo "Assigning ${role_name} at ${scope}..."
  az role assignment create \
    --assignee-object-id "${PIPELINE_OBJECT_ID}" \
    --assignee-principal-type ServicePrincipal \
    --role "${role_name}" \
    --scope "${scope}" \
    --only-show-errors \
    1>/dev/null
  echo "${role_name} assignment created at ${scope}."
}

# Optional resource-scope grants to recover from stale/missing deployer RBAC.
if [[ -n "${RESOURCE_GROUP}" ]]; then
  resource_group_scope="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}"

  if [[ -n "${ACR_NAME}" ]]; then
    acr_scope="${resource_group_scope}/providers/Microsoft.ContainerRegistry/registries/${ACR_NAME}"
    ensure_role_assignment "AcrPush" "${acr_scope}"
  fi

  if [[ -n "${KEYVAULT_NAME}" ]]; then
    kv_scope="${resource_group_scope}/providers/Microsoft.KeyVault/vaults/${KEYVAULT_NAME}"
    ensure_role_assignment "Key Vault Administrator" "${kv_scope}"
  fi

  if [[ -n "${APPCONFIG_NAME}" ]]; then
    appconfig_scope="${resource_group_scope}/providers/Microsoft.AppConfiguration/configurationStores/${APPCONFIG_NAME}"
    ensure_role_assignment "App Configuration Data Owner" "${appconfig_scope}"
  fi
elif [[ -n "${ACR_NAME}" || -n "${KEYVAULT_NAME}" || -n "${APPCONFIG_NAME}" ]]; then
  echo "ERROR: --resource-group is required when using --acr-name, --keyvault-name, or --appconfig-name." >&2
  exit 1
fi

echo
echo "Final subscription-scope assignments for target principal:"
az role assignment list \
  --assignee-object-id "${PIPELINE_OBJECT_ID}" \
  --scope "${SUBSCRIPTION_SCOPE}" \
  --query "[].{role:roleDefinitionName,scope:scope,condition:condition,conditionVersion:conditionVersion}" \
  -o table

echo
echo "Bootstrap complete."
