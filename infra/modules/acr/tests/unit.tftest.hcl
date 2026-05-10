mock_provider "azurerm" {
  mock_resource "azurerm_container_registry" {
    defaults = {
      id           = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.ContainerRegistry/registries/acrbankapidevabcdef"
      login_server = "acrbankapidevabcdef.azurecr.io"
    }
  }
}

variables {
  resource_group_name = "rg-test"
  location            = "eastus"
  app_name            = "bankapi"
  env                 = "dev"
  unique_suffix       = "abcdef"
  acr_sku             = "Basic"
  uami_principal_id   = "00000000-0000-0000-0000-000000000111"
  deployer_object_id  = "00000000-0000-0000-0000-000000000222"
  project_repository_path = "project/fastapi-azure-app"
  tags                = {}
}

run "acr_admin_is_disabled" {
  command = plan

  assert {
    condition     = azurerm_container_registry.acr.admin_enabled == false
    error_message = "ACR admin access must remain disabled."
  }
}

run "uami_has_acr_pull_role" {
  command = plan

  assert {
    condition     = azurerm_role_assignment.acr_pull_uami.role_definition_name == "AcrPull"
    error_message = "The application identity must receive the AcrPull role."
  }
}

run "deployer_has_acr_push_role" {
  command = plan

  assert {
    condition     = azurerm_role_assignment.acr_push_deployer.role_definition_name == "AcrPush"
    error_message = "The deployer must receive the AcrPush role."
  }
}

run "deployer_acr_push_is_abac_scoped_to_project_repository" {
  command = plan

  assert {
    condition     = azurerm_role_assignment.acr_push_deployer.condition_version == "2.0"
    error_message = "The deployer AcrPush role assignment must use condition_version 2.0 when ABAC enforcement is enabled."
  }

  assert {
    condition     = can(regex("project/fastapi-azure-app", azurerm_role_assignment.acr_push_deployer.condition))
    error_message = "The deployer AcrPush ABAC condition must restrict access to the configured project repository path."
  }
}