mock_provider "azurerm" {
  mock_resource "azurerm_container_app_environment" {
    defaults = {
      id = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.App/managedEnvironments/cae-bankapi-dev"
    }
  }

  mock_resource "azurerm_container_app" {
    defaults = {
      latest_revision_fqdn = "ca-bankapi-dev.mock.azurecontainerapps.io"
    }
  }
}

variables {
  resource_group_name                 = "rg-test"
  location                            = "eastus"
  app_name                            = "bankapi"
  env                                 = "dev"
  log_analytics_workspace_id          = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.OperationalInsights/workspaces/log-bankapi-dev"
  container_image                     = "example.azurecr.io/bank-api:latest"
  uami_id                             = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-bankapi-dev"
  uami_client_id                      = "00000000-0000-0000-0000-000000000123"
  appinsights_secret_versionless_id   = "https://kv-test.vault.azure.net/secrets/appinsights-connection-string"
  smtp_password_secret_versionless_id = "https://kv-test.vault.azure.net/secrets/smtp-password"
  cosmos_account_url                  = "https://cosmos-test.documents.azure.com:443/"
  cosmos_db_name                      = "banking"
  app_config_endpoint                 = "https://appcs-bankapi-dev.azconfig.io"
  key_vault_uri                       = "https://kv-test.vault.azure.net/"
  smtp_host                           = "smtp.office365.com"
  smtp_port                           = 587
  smtp_username                       = "noreply@example.com"
  smtp_from_email                     = "noreply@example.com"
  tags                                = {}
}

run "smtp_secret_is_wired" {
  command = plan

  assert {
    condition     = length([for s in azurerm_container_app.app.secret : s if s.name == "smtp-password"]) == 1
    error_message = "Container App must include an SMTP Key Vault-backed secret named 'smtp-password'."
  }
}

run "smtp_password_env_uses_secret" {
  command = plan

  assert {
    condition     = length([for e in azurerm_container_app.app.template[0].container[0].env : e if e.name == "SMTP_PASSWORD" && e.secret_name == "smtp-password"]) == 1
    error_message = "SMTP_PASSWORD environment variable must reference the smtp-password secret."
  }
}