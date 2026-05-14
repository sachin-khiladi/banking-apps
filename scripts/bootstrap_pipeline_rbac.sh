#!/usr/bin/env bash
set -euo pipefail

# Manual prerequisite bootstrap for Terraform pipeline identity.
# Run this with a privileged operator identity (Owner or User Access Administrator)
# before enabling rbac_bootstrap in terraform.tfvars.

readonly PIPELINE_CLIENT_ID="05baf6a1-cae6-442a-94d6-f0d1f64b61f4"
readonly PIPELINE_OBJECT_ID="cd7ca1e6-67f4-4120-b3a2-615de398cc6a"

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

SUBSCRIPTION_ID="${1:-$(az account show --query id -o tsv)}"
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

echo
echo "Final subscription-scope assignments for target principal:"
az role assignment list \
  --assignee-object-id "${PIPELINE_OBJECT_ID}" \
  --scope "${SUBSCRIPTION_SCOPE}" \
  --query "[].{role:roleDefinitionName,scope:scope,condition:condition,conditionVersion:conditionVersion}" \
  -o table

echo
echo "Bootstrap complete."
