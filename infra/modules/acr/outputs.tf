output "acr_id" {
  description = "Azure Container Registry resource ID"
  value       = azurerm_container_registry.acr.id
}

output "acr_name" {
  description = "Azure Container Registry name"
  value       = azurerm_container_registry.acr.name
}

output "login_server" {
  description = "ACR login server FQDN (e.g. acrbankapidev c8775a.azurecr.io)"
  value       = azurerm_container_registry.acr.login_server
}
