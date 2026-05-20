mock_provider "azurerm" {
  mock_resource "azurerm_container_registry" {
    defaults = {
      id           = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.ContainerRegistry/registries/acrbankapidevabcdef"
      login_server = "acrbankapidevabcdef.azurecr.io"
    }
  }
}

variables {
  resource_group_name              = "rg-test"
  location                         = "eastus"
  app_name                         = "bankapi"
  env                              = "dev"
  unique_suffix                    = "abcdef"
  acr_sku                          = "Basic"
  uami_principal_id                = "00000000-0000-0000-0000-000000000111"
  enforce_acr_role_assignment_mode = false
  tags                             = {}
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