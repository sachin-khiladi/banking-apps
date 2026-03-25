output "endpoint" {
  description = "App Configuration endpoint URL"
  value       = azurerm_app_configuration.appconfig.endpoint
}

output "id" {
  description = "App Configuration resource ID"
  value       = azurerm_app_configuration.appconfig.id
}
