# ===========================================================================
# Module: appconfig
# Provisions: Azure App Configuration + RBAC + seed key-values
# ===========================================================================

resource "azurerm_app_configuration" "appconfig" {
  name                       = "appcs-${var.app_name}-${var.env}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  sku                        = var.app_config_sku
  soft_delete_retention_days = var.soft_delete_retention_days

  tags = var.tags
}

# ---------------------------------------------------------------------------
# RBAC — deploying principal → Data Owner (write key-values via Terraform)
# The deployer is a CI/CD service principal; skip_service_principal_aad_check
# prevents the provider from polling AAD for propagation, which avoids
# intermittent 400/403 errors when the identity was recently created or
# re-granted.
# ---------------------------------------------------------------------------
resource "azurerm_role_assignment" "appconfig_owner_deployer" {
  scope                = azurerm_app_configuration.appconfig.id
  role_definition_name = "App Configuration Data Owner"
  principal_id         = var.deployer_object_id

  skip_service_principal_aad_check = true

  lifecycle {
    ignore_changes = [
      # Provider-only flag; Azure never persists it — ignore to prevent
      # perpetual "update" cycles after import or provider version changes.
      skip_service_principal_aad_check,
      # Computed alongside role_definition_name; may vary across provider
      # versions without a real config change.
      role_definition_id,
    ]
  }
}

# ---------------------------------------------------------------------------
# RBAC — UAMI → Data Reader (runtime read-only access)
# ---------------------------------------------------------------------------
resource "azurerm_role_assignment" "appconfig_reader_app" {
  scope                = azurerm_app_configuration.appconfig.id
  role_definition_name = "App Configuration Data Reader"
  principal_id         = var.app_identity_principal_id
}

# ---------------------------------------------------------------------------
# Seed key-values (non-secret, env-scoped)
# ---------------------------------------------------------------------------
resource "azurerm_app_configuration_key" "environment" {
  configuration_store_id = azurerm_app_configuration.appconfig.id
  key                    = "app:environment"
  value                  = var.env
  label                  = var.env

  depends_on = [azurerm_role_assignment.appconfig_owner_deployer]
}

resource "azurerm_app_configuration_key" "app_name" {
  configuration_store_id = azurerm_app_configuration.appconfig.id
  key                    = "app:name"
  value                  = var.app_name
  label                  = var.env

  depends_on = [azurerm_role_assignment.appconfig_owner_deployer]
}
