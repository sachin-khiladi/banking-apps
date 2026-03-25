output "key_vault_id" {
  description = "Key Vault resource ID"
  value       = azurerm_key_vault.kv.id
}

output "key_vault_name" {
  description = "Key Vault name"
  value       = azurerm_key_vault.kv.name
}

output "key_vault_uri" {
  description = "Key Vault URI (https://<name>.vault.azure.net/)"
  value       = azurerm_key_vault.kv.vault_uri
}

output "uami_id" {
  description = "Resource ID of the User-Assigned Managed Identity"
  value       = azurerm_user_assigned_identity.app_identity.id
}

output "uami_client_id" {
  description = "Client ID of the UAMI (pass as AZURE_CLIENT_ID to the app)"
  value       = azurerm_user_assigned_identity.app_identity.client_id
}

output "uami_principal_id" {
  description = "Object/Principal ID of the UAMI"
  value       = azurerm_user_assigned_identity.app_identity.principal_id
}

output "appinsights_secret_versionless_id" {
  description = "Versionless KV secret URI for the App Insights connection string"
  value       = azurerm_key_vault_secret.appinsights_connection_string.versionless_id
}

output "smtp_password_secret_versionless_id" {
  description = "Versionless KV secret URI for the SMTP password"
  value       = azurerm_key_vault_secret.smtp_password.versionless_id
}

# cosmos_secret_versionless_id removed — app uses RBAC auth, not a KV secret.
