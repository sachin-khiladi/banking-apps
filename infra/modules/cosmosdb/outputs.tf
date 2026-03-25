output "account_name" {
  description = "Cosmos DB account name"
  value       = azurerm_cosmosdb_account.cosmos.name
}

output "account_id" {
  description = "Cosmos DB account resource ID (used to construct role definition IDs for RBAC)"
  value       = azurerm_cosmosdb_account.cosmos.id
}

output "account_endpoint" {
  description = "Cosmos DB account endpoint URL — set as COSMOS_ACCOUNT_URL in the application"
  value       = azurerm_cosmosdb_account.cosmos.endpoint
}

output "db_name" {
  description = "SQL database name — set as COSMOS_DB_NAME in the application"
  value       = azurerm_cosmosdb_sql_database.db.name
}

output "container_name" {
  description = "SQL container name"
  value       = azurerm_cosmosdb_sql_container.accounts.name
}

output "user_profiles_container_name" {
  description = "SQL container name for user profiles"
  value       = azurerm_cosmosdb_sql_container.user_profiles.name
}

output "primary_key" {
  description = "Primary master key — use only for emergency break-glass; prefer RBAC auth in the app"
  value       = azurerm_cosmosdb_account.cosmos.primary_key
  sensitive   = true
}
