output "id" {
  description = "Resource ID of the Storage Account."
  value       = azurerm_storage_account.main.id
}

output "name" {
  description = "Storage Account name."
  value       = azurerm_storage_account.main.name
}

output "primary_blob_endpoint" {
  description = "Primary Blob endpoint for the Storage Account."
  value       = azurerm_storage_account.main.primary_blob_endpoint
}
