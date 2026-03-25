output "log_analytics_workspace_id" {
  description = "Resource ID of the Log Analytics Workspace"
  value       = azurerm_log_analytics_workspace.law.id
}

output "app_insights_name" {
  description = "Application Insights resource name"
  value       = azurerm_application_insights.appinsights.name
}

output "app_insights_instrumentation_key" {
  description = "Application Insights instrumentation key (legacy SDK)"
  value       = azurerm_application_insights.appinsights.instrumentation_key
  sensitive   = true
}

output "app_insights_connection_string" {
  description = "Application Insights connection string (OpenTelemetry / modern SDK)"
  value       = azurerm_application_insights.appinsights.connection_string
  sensitive   = true
}
