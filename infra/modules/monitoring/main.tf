# ===========================================================================
# Module: monitoring
# Provisions: Log Analytics Workspace + Application Insights (workspace-based)
# ===========================================================================

resource "azurerm_log_analytics_workspace" "law" {
  name                = "log-${var.app_name}-${var.env}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days

  tags = var.tags
}

resource "azurerm_application_insights" "appinsights" {
  name                = "appi-${var.app_name}-${var.env}"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.law.id
  application_type    = "web"

  tags = var.tags
}
