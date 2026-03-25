mock_provider "azurerm" {
  mock_resource "azurerm_key_vault" {
    defaults = {
      id        = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.KeyVault/vaults/kv-bankapi-dev-abcdef"
      vault_uri = "https://kv-bankapi-dev-abcdef.vault.azure.net/"
    }
  }

  mock_resource "azurerm_key_vault_secret" {
    defaults = {
      versionless_id = "https://kv-bankapi-dev-abcdef.vault.azure.net/secrets/mock"
    }
  }

  mock_resource "azurerm_user_assigned_identity" {
    defaults = {
      id           = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-bankapi-dev"
      principal_id = "00000000-0000-0000-0000-000000000123"
      client_id    = "00000000-0000-0000-0000-000000000124"
    }
  }
}

variables {
  resource_group_name            = "rg-test"
  location                       = "eastus"
  app_name                       = "bankapi"
  env                            = "dev"
  unique_suffix                  = "abcdef"
  tenant_id                      = "00000000-0000-0000-0000-000000000001"
  deployer_object_id             = "00000000-0000-0000-0000-000000000002"
  app_insights_connection_string = "InstrumentationKey=mock"
  smtp_password                  = "mock-smtp-password"
  tags                           = {}
}

run "smtp_secret_name" {
  command = plan

  assert {
    condition     = azurerm_key_vault_secret.smtp_password.name == "smtp-password"
    error_message = "SMTP Key Vault secret name must be 'smtp-password'."
  }
}

run "smtp_secret_output_is_versionless" {
  command = plan

  assert {
    condition     = startswith(output.smtp_password_secret_versionless_id, "https://") && strcontains(output.smtp_password_secret_versionless_id, "/secrets/")
    error_message = "smtp_password_secret_versionless_id must be a Key Vault secret URI."
  }
}