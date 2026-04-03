mock_provider "azurerm" {
  mock_resource "azurerm_role_assignment" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-bankapi-dev/providers/Microsoft.Authorization/roleAssignments/00000000-0000-0000-0000-000000000111"
    }
  }
}

variables {
  resource_group_id              = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-bankapi-dev"
  deployment_principal_object_id = "00000000-0000-0000-0000-000000000123"
}

run "default_roles_include_required_bootstrap_roles" {
  command = plan

  assert {
    condition     = contains(output.assigned_role_definition_names, "User Access Administrator")
    error_message = "Bootstrap roles must include 'User Access Administrator'."
  }

  assert {
    condition     = contains(output.assigned_role_definition_names, "Contributor")
    error_message = "Bootstrap roles must include 'Contributor'."
  }
}

run "default_assignments_count_is_two" {
  command = plan

  assert {
    condition     = length(output.role_assignment_ids) == 2
    error_message = "Bootstrap module must create exactly two role assignments by default."
  }
}

run "skip_sp_aad_check_is_true_by_default" {
  command = plan

  assert {
    condition     = alltrue([for ra in azurerm_role_assignment.bootstrap : ra.skip_service_principal_aad_check == true])
    error_message = "All bootstrap role assignments must have skip_service_principal_aad_check = true to avoid AAD propagation delays for CI/CD service principals."
  }
}

run "disabled_module_creates_no_assignments" {
  command = plan

  variables {
    enabled = false
  }

  assert {
    condition     = length(output.role_assignment_ids) == 0
    error_message = "Bootstrap module must create no role assignments when enabled = false."
  }
}

run "uaa_condition_applied_only_to_user_access_administrator" {
  command = plan

  variables {
    uaa_condition = "!(ActionMatches{'Microsoft.Authorization/roleAssignments/write'}) OR @Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {b24988ac-6180-42a0-ab88-20f7382dd24c}"
  }

  assert {
    condition     = azurerm_role_assignment.bootstrap["User Access Administrator"].condition != null
    error_message = "ABAC condition must be set on the User Access Administrator role assignment when uaa_condition is provided."
  }

  assert {
    condition     = azurerm_role_assignment.bootstrap["User Access Administrator"].condition == "!(ActionMatches{'Microsoft.Authorization/roleAssignments/write'}) OR @Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {b24988ac-6180-42a0-ab88-20f7382dd24c}"
    error_message = "ABAC condition value must match the uaa_condition input variable."
  }

  assert {
    condition     = azurerm_role_assignment.bootstrap["Contributor"].condition == null
    error_message = "ABAC condition must NOT be set on the Contributor role assignment."
  }
}

run "uaa_condition_is_null_by_default" {
  command = plan

  variables {
    role_definition_names = ["User Access Administrator", "Contributor"]
  }

  assert {
    condition     = azurerm_role_assignment.bootstrap["User Access Administrator"].condition == null
    error_message = "ABAC condition must be null for User Access Administrator when uaa_condition is not provided."
  }
}