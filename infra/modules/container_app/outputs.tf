output "container_app_environment_id" {
  description = "Container App Environment resource ID"
  value       = azurerm_container_app_environment.cae.id
}

output "container_app_fqdn" {
  description = "Canonical ingress fully-qualified domain name of the Container App"
  value       = azurerm_container_app.app.ingress[0].fqdn
}

output "container_app_active_revision" {
  description = "Latest ready/active Container App revision name"
  value       = azurerm_container_app.app.latest_revision_name
}

output "container_app_url" {
  description = "Public HTTPS URL of the Container App"
  value       = "https://${azurerm_container_app.app.ingress[0].fqdn}"
}
