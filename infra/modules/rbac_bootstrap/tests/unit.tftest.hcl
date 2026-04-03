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