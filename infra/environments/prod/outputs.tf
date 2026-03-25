output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
}

output "log_analytics_workspace_id" {
  value = module.monitoring.log_analytics_workspace_id
}

output "app_insights_name" {
  value = module.monitoring.app_insights_name
}

output "app_insights_connection_string" {
  value     = module.monitoring.app_insights_connection_string
  sensitive = true
}

output "key_vault_name" {
  value = module.keyvault.key_vault_name
}

output "key_vault_uri" {
  value = module.keyvault.key_vault_uri
}

output "uami_client_id" {
  description = "AZURE_CLIENT_ID to set in application configuration"
  value       = module.keyvault.uami_client_id
}

output "app_config_endpoint" {
  value = module.appconfig.endpoint
}

output "container_app_url" {
  value = module.container_app.container_app_url
}

output "container_app_fqdn" {
  value = module.container_app.container_app_fqdn
}

output "container_app_active_revision" {
  description = "Container App latest ready/active revision name"
  value       = module.container_app.container_app_active_revision
}

output "acr_name" {
  description = "ACR name — use with: az acr login --name <acr_name>"
  value       = module.acr.acr_name
}

output "acr_login_server" {
  description = "ACR login server — prefix for docker tag/push"
  value       = module.acr.login_server
}

output "docker_push_command" {
  description = "Example docker push command for this environment"
  value       = "docker push ${module.acr.login_server}/bank-api:stable"
}

# ---------------------------------------------------------------------------
# Storage Account
# ---------------------------------------------------------------------------

output "storage_account_name" {
  description = "Storage Account name"
  value       = module.storage_account.name
}

output "storage_account_id" {
  description = "Storage Account resource ID"
  value       = module.storage_account.id
}

output "storage_account_blob_endpoint" {
  description = "Storage Account primary Blob endpoint"
  value       = module.storage_account.primary_blob_endpoint
}

# ---------------------------------------------------------------------------
# Cosmos DB
# ---------------------------------------------------------------------------

output "cosmos_account_name" {
  description = "Cosmos DB account name"
  value       = module.cosmosdb.account_name
}

output "cosmos_endpoint" {
  description = "Cosmos DB endpoint — value of COSMOS_ACCOUNT_URL"
  value       = module.cosmosdb.account_endpoint
}

output "cosmos_db_name" {
  description = "SQL database name — value of COSMOS_DB_NAME"
  value       = module.cosmosdb.db_name
}
