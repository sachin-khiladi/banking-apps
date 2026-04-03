# Module: rbac_bootstrap

Bootstraps management-plane RBAC at resource-group scope for the deployment
principal so downstream role assignments can be created without
`AuthorizationFailed` on `Microsoft.Authorization/roleAssignments/write`.

## Resources Created

- `azurerm_role_assignment.bootstrap` — assigns required built-in roles to the
  deployment principal.

## Usage

```hcl
module "rbac_bootstrap" {
  source = "../../modules/rbac_bootstrap"

  enabled                         = var.rbac_bootstrap_enabled
  resource_group_id               = azurerm_resource_group.main.id
  deployment_principal_object_id  = local.deployment_principal_object_id
  role_definition_names           = var.rbac_bootstrap_role_definition_names
  skip_service_principal_aad_check = var.rbac_bootstrap_skip_sp_aad_check
}
```

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| enabled | bool | ❌ | Toggle to enable or disable bootstrap role-assignment creation. |
| resource_group_id | string | ✅ | Resource ID of the resource group scope for bootstrap role assignments. |
| deployment_principal_object_id | string | ✅ | Object ID of the deployment principal to grant bootstrap RBAC. |
| role_definition_names | list(string) | ❌ | Built-in role names assigned at RG scope. Defaults to `User Access Administrator` and `Contributor`. |
| skip_service_principal_aad_check | bool | ❌ | Skip AAD service principal propagation checks during role assignment creation. |

## Outputs

| Name | Type | Description |
|---|---|---|
| role_assignment_ids | map(string) | Map of role name → role assignment ID. |
| assigned_role_definition_names | list(string) | Sorted list of roles assigned by the module. |
| deployment_principal_object_id | string | Principal object ID passed to the module. |