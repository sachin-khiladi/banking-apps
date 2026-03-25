mock_provider "azurerm" {
  mock_resource "azurerm_storage_account" {
    defaults = {
      id                    = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.Storage/storageAccounts/stbankapidevabcdef"
      primary_blob_endpoint = "https://stbankapidevabcdef.blob.core.windows.net/"
    }
  }
}

variables {
  resource_group_name = "rg-test"
  location            = "eastus"
  app_name            = "bankapi"
  env                 = "dev"
  unique_suffix       = "abcdef"
  tags                = {}
}

run "storage_account_name_prefix" {
  command = plan

  assert {
    condition     = startswith(azurerm_storage_account.main.name, "st")
    error_message = "Storage account name must start with 'st'."
  }
}

run "storage_account_name_length" {
  command = plan

  assert {
    condition     = length(azurerm_storage_account.main.name) <= 24
    error_message = "Storage account name must be 24 characters or fewer."
  }
}
