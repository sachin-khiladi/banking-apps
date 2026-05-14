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

mock_provider "time" {}

variables {
  resource_group_name            = "rg-test"
  location                       = "eastus"
  app_name                       = "bankapi"
  env                            = "dev"
  unique_suffix                  = "abcdef"
  tenant_id                      = "00000000-0000-0000-0000-000000000001"
  deployer_object_id             = "00000000-0000-0000-0000-000000000002"
  app_insights_connection_string = "InstrumentationKey=mock"
  jwt_secret_key                 = "mock-jwt-secret"
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

run "jwt_secret_name" {
  command = plan

  assert {
    condition     = azurerm_key_vault_secret.jwt_secret_key.name == "jwt-secret-key"
    error_message = "JWT Key Vault secret name must be 'jwt-secret-key'."
  }
}

run "appinsights_secret_name" {
  command = plan

  assert {
    condition     = azurerm_key_vault_secret.appinsights_connection_string.name == "appinsights-connection-string"
    error_message = "App Insights Key Vault secret name must be 'appinsights-connection-string'."
  }
}

run "key_vault_uses_rbac_authorization" {
  command = plan

  assert {
    condition     = azurerm_key_vault.kv.enable_rbac_authorization == true
    error_message = "Key Vault must use RBAC authorization."
  }
}

run "kv_admin_deployer_skips_aad_check" {
  command = plan

  assert {
    condition     = azurerm_role_assignment.kv_admin_deployer.skip_service_principal_aad_check == true
    error_message = "kv_admin_deployer role assignment must set skip_service_principal_aad_check = true for CI/CD service principal deployers to avoid AAD propagation delays."
  }
}

run "kv_runtime_reader_skips_aad_check" {
  command = plan

  assert {
    condition     = azurerm_role_assignment.kv_secrets_user_app.skip_service_principal_aad_check == true
    error_message = "kv_secrets_user_app role assignment must set skip_service_principal_aad_check = true to avoid UAMI propagation timing failures."
  }
}

run "kv_rbac_propagation_wait_default" {
  command = plan

  assert {
    condition     = time_sleep.wait_for_kv_admin_rbac.create_duration == "90s"
    error_message = "Key Vault module must wait for deployer RBAC propagation before secret operations."
  }
}