# Module: rbac_bootstrap

Bootstraps management-plane RBAC at resource-group scope for the deployment
principal so downstream role assignments can be created without
`AuthorizationFailed` on `Microsoft.Authorization/roleAssignments/write`.

## ⚠️  Bootstrap Prerequisite (Read Before Enabling)

This module suffers from a **circular bootstrap dependency**: the principal that
runs Terraform must already hold `Microsoft.Authorization/roleAssignments/write`
(e.g. `User Access Administrator` or `Owner`) **before** it can assign those
roles to itself.

**Never enable this module (`enabled = true`) when running as the same service
principal that needs the resulting roles** — it will fail with HTTP 403.

### How to satisfy the prerequisite

Run once by a privileged Azure admin (not the CI SP):

```bash
# Replace SUBSCRIPTION_ID and CI_SP_OBJECT_ID with real values.
az role assignment create \
  --role "User Access Administrator" \
  --assignee-object-id <CI_SP_OBJECT_ID> \
  --assignee-principal-type ServicePrincipal \
  --scope /subscriptions/<SUBSCRIPTION_ID>
```

> **Security tip**: use the `--condition` and `--condition-version "2.0"` flags
> to constrain the role to only the specific built-in role definition IDs your
> pipeline needs to assign. Pass the same condition string via `var.uaa_condition`
> when you enable this module.

Once the CI SP has the subscription-scoped role, set `enabled = true` in your
environment `terraform.tfvars` and re-run the pipeline.

## Resources Created

- `azurerm_role_assignment.bootstrap` — assigns required built-in roles to the
  deployment principal at resource-group scope.

## Usage

```hcl
module "rbac_bootstrap" {
  source = "../../modules/rbac_bootstrap"

  enabled                          = var.rbac_bootstrap_enabled
  resource_group_id                = azurerm_resource_group.main.id
  deployment_principal_object_id   = local.deployment_principal_object_id
  role_definition_names            = var.rbac_bootstrap_role_definition_names
  skip_service_principal_aad_check = var.rbac_bootstrap_skip_sp_aad_check

  # Recommended: constrain User Access Administrator via ABAC condition to
  # prevent privilege escalation. Omit or set null to create an unconditioned
  # assignment (only acceptable when scope is already tightly controlled).
  uaa_condition = var.rbac_bootstrap_uaa_condition
}
```

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| enabled | bool | ❌ | Toggle to enable or disable bootstrap role-assignment creation. **Default: false** |
| resource_group_id | string | ✅ | Resource ID of the resource group scope for bootstrap role assignments. |
| deployment_principal_object_id | string | ✅ | Object ID of the deployment principal to grant bootstrap RBAC. |
| role_definition_names | list(string) | ❌ | Built-in role names assigned at RG scope. Defaults to `User Access Administrator` and `Contributor`. |
| skip_service_principal_aad_check | bool | ❌ | Skip AAD service principal propagation checks during role assignment creation. |
| uaa_condition | string | ❌ | ABAC condition expression (v2.0) applied to the `User Access Administrator` assignment to constrain which roles can be assigned. `null` skips the condition. |

## Outputs

| Name | Type | Description |
|---|---|---|
| role_assignment_ids | map(string) | Map of role name → role assignment ID. |
| assigned_role_definition_names | list(string) | Sorted list of roles assigned by the module. |
| deployment_principal_object_id | string | Principal object ID passed to the module. |