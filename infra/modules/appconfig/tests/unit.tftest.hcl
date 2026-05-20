mock_provider "azurerm" {
  mock_resource "azurerm_app_configuration" {
    defaults = {
      id       = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.AppConfiguration/configurationStores/appcs-bankapi-dev"
      endpoint = "https://appcs-bankapi-dev.azconfig.io"
    }
  }
}

mock_provider "time" {}

variables {
  resource_group_name        = "rg-test"
  location                   = "eastus"
  app_name                   = "bankapi"
  env                        = "dev"
  app_identity_principal_id  = "00000000-0000-0000-0000-000000000222"
  app_config_sku             = "standard"
  soft_delete_retention_days = 7
  tags                       = {}
}

run "appconfig_name_matches_convention" {
  command = plan

  assert {
    condition     = azurerm_app_configuration.appconfig.name == "appcs-bankapi-dev"
    error_message = "App Configuration name must follow the appcs-<app>-<env> convention."
  }
}

run "app_identity_has_data_reader_role" {
  command = plan

  assert {
    condition     = azurerm_role_assignment.appconfig_reader_app.role_definition_name == "App Configuration Data Reader"
    error_message = "The application identity must receive the App Configuration Data Reader role."
  }
}

run "app_reader_assignment_skips_aad_check" {
  command = plan

  assert {
    condition     = azurerm_role_assignment.appconfig_reader_app.skip_service_principal_aad_check == true
    error_message = "App Configuration Data Reader assignment must set skip_service_principal_aad_check = true to avoid UAMI propagation timing failures."
  }
}