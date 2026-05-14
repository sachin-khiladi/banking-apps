# ===========================================================================
# Module: keyvault
# Provisions: User-Assigned Managed Identity + Key Vault (RBAC mode) + Secrets
# ===========================================================================

terraform {
  required_providers {
    time = {
      source  = "hashicorp/time"
      version = "~> 0.11"
    }
  }
}

# ---------------------------------------------------------------------------
# User-Assigned Managed Identity
# Created here so the Container App module can attach it without a circular
# dependency between the CA and Key Vault.
# ---------------------------------------------------------------------------
resource "azurerm_user_assigned_identity" "app_identity" {
  name                = "id-${var.app_name}-${var.env}"
  location            = var.location
  resource_group_name = var.resource_group_name

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Key Vault
# ---------------------------------------------------------------------------
resource "azurerm_key_vault" "kv" {
  # max 24 chars; keep it deterministic with the unique_suffix
  name                       = "kv-${var.app_name}-${var.env}-${var.unique_suffix}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  tenant_id                  = var.tenant_id
  sku_name                   = var.kv_sku
  soft_delete_retention_days = var.kv_soft_delete_retention_days

  enable_rbac_authorization = true
  purge_protection_enabled  = var.purge_protection_enabled

  tags = var.tags

  lifecycle {
    precondition {
      condition     = length("kv-${var.app_name}-${var.env}-${var.unique_suffix}") <= 24
      error_message = "The generated Key Vault name exceeds Azure's 24-character limit. Shorten app_name/env or change the naming strategy before apply."
    }
  }
}

# ---------------------------------------------------------------------------
# RBAC — deploying principal → Key Vault Administrator
# Required so Terraform can write secrets.
# The deployer is a CI/CD service principal; skip_service_principal_aad_check
# prevents the provider from polling AAD for propagation, which avoids
# intermittent 400/403 errors when the identity was recently created or
# re-granted.
# ---------------------------------------------------------------------------
resource "azurerm_role_assignment" "kv_admin_deployer" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = var.deployer_object_id

  skip_service_principal_aad_check = true

  lifecycle {
    ignore_changes = [
      # Provider-only flag; Azure never persists it — ignore to prevent
      # perpetual "update" cycles after provider version changes.
      skip_service_principal_aad_check,
      # Computed alongside role_definition_name; may vary across provider
      # versions without a real config change.
      role_definition_id,
    ]
  }
}

# Key Vault data-plane RBAC can take time to propagate after role assignment.
# Delay secret reads/writes to avoid transient 403 ForbiddenByRbac failures.
resource "time_sleep" "wait_for_kv_admin_rbac" {
  depends_on      = [azurerm_role_assignment.kv_admin_deployer]
  create_duration = "${var.rbac_propagation_wait_seconds}s"
}

# ---------------------------------------------------------------------------
# RBAC — UAMI → Key Vault Secrets User (read-only at runtime)
# ---------------------------------------------------------------------------
resource "azurerm_role_assignment" "kv_secrets_user_app" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.app_identity.principal_id
}

# ---------------------------------------------------------------------------
# Secrets
# ---------------------------------------------------------------------------

resource "azurerm_key_vault_secret" "appinsights_connection_string" {
  name         = "appinsights-connection-string"
  value        = var.app_insights_connection_string
  key_vault_id = azurerm_key_vault.kv.id

  tags = var.tags

  # Wait for deployer to have write access AND the UAMI read role to be assigned
  # so both the secret write and the runtime read path are ready atomically.
  depends_on = [
    time_sleep.wait_for_kv_admin_rbac,
    azurerm_role_assignment.kv_secrets_user_app,
  ]

  lifecycle {
    precondition {
      condition     = trimspace(var.app_insights_connection_string) != ""
      error_message = "app_insights_connection_string must not be empty before creating the Key Vault secret."
    }
  }
}

resource "azurerm_key_vault_secret" "jwt_secret_key" {
  name         = "jwt-secret-key"
  value        = var.jwt_secret_key
  key_vault_id = azurerm_key_vault.kv.id

  tags = var.tags

  depends_on = [
    time_sleep.wait_for_kv_admin_rbac,
    azurerm_role_assignment.kv_secrets_user_app,
  ]

  lifecycle {
    precondition {
      condition     = trimspace(var.jwt_secret_key) != ""
      error_message = "jwt_secret_key must not be empty before creating the Key Vault secret."
    }
  }
}

resource "azurerm_key_vault_secret" "smtp_password" {
  name         = "smtp-password"
  value        = var.smtp_password
  key_vault_id = azurerm_key_vault.kv.id

  tags = var.tags

  depends_on = [
    time_sleep.wait_for_kv_admin_rbac,
    azurerm_role_assignment.kv_secrets_user_app,
  ]

  lifecycle {
    precondition {
      condition     = trimspace(var.smtp_password) != ""
      error_message = "smtp_password must not be empty before creating the Key Vault secret."
    }
  }
}

# cosmos-connection-string secret intentionally omitted:
# The app authenticates to Cosmos DB via DefaultAzureCredential (RBAC).
# COSMOS_ACCOUNT_URL and COSMOS_DB_NAME are plain (non-secret) env vars
# injected directly into the Container App — no KV secret needed.
