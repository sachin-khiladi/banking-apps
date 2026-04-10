# ===========================================================================
# environments/dev — Root module
# Wires together all child modules for the dev environment.
# ===========================================================================

data "azurerm_client_config" "current" {}

locals {
  app_name      = "bankapi"
  unique_suffix = substr(data.azurerm_client_config.current.subscription_id, 27, 6)
  deployment_principal_object_id = coalesce(
    var.deployment_principal_object_id,
    data.azurerm_client_config.current.object_id,
  )

  # cosmos_location falls back to the primary region when not explicitly overridden.
  # Override in tfvars to work around regional capacity constraints (e.g. East US AZ quota).
  cosmos_location = coalesce(var.cosmos_location, var.location)

  common_tags = {
    environment = var.env
    application = local.app_name
    managed_by  = "terraform"
    cost-center = var.cost_center
    owner       = "platform-team"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.app_name}-${var.env}"
  location = var.location
  tags     = local.common_tags
}

# ---------------------------------------------------------------------------
# RBAC bootstrap for deployment principal (management-plane role assignment rights)
# ---------------------------------------------------------------------------
module "rbac_bootstrap" {
  source = "../../modules/rbac_bootstrap"

  enabled                          = var.rbac_bootstrap_enabled
  resource_group_id                = azurerm_resource_group.main.id
  deployment_principal_object_id   = local.deployment_principal_object_id
  role_definition_names            = var.rbac_bootstrap_role_definition_names
  skip_service_principal_aad_check = var.rbac_bootstrap_skip_sp_aad_check
}

# ---------------------------------------------------------------------------
# Storage Account
# ---------------------------------------------------------------------------
module "storage_account" {
  source = "../../modules/storage_account"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  app_name            = local.app_name
  env                 = var.env
  unique_suffix       = local.unique_suffix

  account_tier             = var.storage_account_tier
  account_replication_type = var.storage_account_replication_type
  access_tier              = var.storage_account_access_tier
  enable_hns               = var.storage_account_enable_hns
  allow_blob_public_access = var.storage_account_allow_blob_public_access

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# Monitoring — Log Analytics + Application Insights
# ---------------------------------------------------------------------------
module "monitoring" {
  source = "../../modules/monitoring"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  app_name            = local.app_name
  env                 = var.env
  log_retention_days  = var.log_retention_days
  tags                = local.common_tags
}

# ---------------------------------------------------------------------------
# Cosmos DB — account, database, container + deployer RBAC
# Depends on rbac_bootstrap so the deployment principal holds the Contributor
# role (needed for Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments/write)
# before the Cosmos DB SQL role assignment is attempted.
# ---------------------------------------------------------------------------
module "cosmosdb" {
  source = "../../modules/cosmosdb"

  depends_on = [module.rbac_bootstrap]

  resource_group_name      = azurerm_resource_group.main.name
  location                 = local.cosmos_location
  app_name                 = local.app_name
  env                      = var.env
  unique_suffix            = local.unique_suffix
  enable_serverless        = var.enable_serverless
  db_name                  = var.cosmos_db_name
  deployer_object_id       = local.deployment_principal_object_id
  app_uami_principal_id    = module.keyvault.uami_principal_id
  assign_app_cosmosdb_role = true
  tags                     = local.common_tags
}

# ---------------------------------------------------------------------------
# Key Vault + UAMI + Secrets
# ---------------------------------------------------------------------------

module "keyvault" {
  source = "../../modules/keyvault"

  depends_on = [module.rbac_bootstrap]

  resource_group_name            = azurerm_resource_group.main.name
  location                       = azurerm_resource_group.main.location
  app_name                       = local.app_name
  env                            = var.env
  unique_suffix                  = local.unique_suffix
  tenant_id                      = data.azurerm_client_config.current.tenant_id
  deployer_object_id             = local.deployment_principal_object_id
  kv_sku                         = var.kv_sku
  kv_soft_delete_retention_days  = var.kv_soft_delete_retention_days
  purge_protection_enabled       = var.purge_protection_enabled
  app_insights_connection_string = module.monitoring.app_insights_connection_string
  jwt_secret_key                 = var.jwt_secret_key
  smtp_password                  = var.smtp_password
  tags                           = local.common_tags
}

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
module "appconfig" {
  source = "../../modules/appconfig"

  depends_on = [module.rbac_bootstrap]

  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  app_name                   = local.app_name
  env                        = var.env
  deployer_object_id         = local.deployment_principal_object_id
  app_identity_principal_id  = module.keyvault.uami_principal_id
  app_config_sku             = var.app_config_sku
  soft_delete_retention_days = var.app_config_soft_delete_days
  tags                       = local.common_tags
}

# ---------------------------------------------------------------------------
# Azure Container Registry + AcrPull grant to UAMI
# ---------------------------------------------------------------------------
module "acr" {
  source = "../../modules/acr"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  app_name            = local.app_name
  env                 = var.env
  unique_suffix       = local.unique_suffix
  acr_sku             = var.acr_sku
  uami_principal_id   = module.keyvault.uami_principal_id
  deployer_object_id  = local.deployment_principal_object_id
  tags                = local.common_tags

  # UAMI must exist before we can assign the AcrPull role
  depends_on = [module.keyvault]
}

# ---------------------------------------------------------------------------
# Container App Environment + Container App
# ---------------------------------------------------------------------------

module "container_app" {
  source = "../../modules/container_app"

  # Explicit ordering: KV secrets, App Config RBAC, and ACR AcrPull role
  # must all be propagated in Azure before the container starts.
  depends_on = [
    module.keyvault,
    module.appconfig,
    module.acr,
    module.cosmosdb,
  ]

  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  app_name                   = local.app_name
  env                        = var.env
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id

  container_image  = var.container_image
  container_cpu    = var.container_cpu
  container_memory = var.container_memory
  min_replicas     = var.min_replicas
  max_replicas     = var.max_replicas
  container_port   = var.container_port

  uami_id        = module.keyvault.uami_id
  uami_client_id = module.keyvault.uami_client_id

  appinsights_secret_versionless_id    = module.keyvault.appinsights_secret_versionless_id
  jwt_secret_key_secret_versionless_id = module.keyvault.jwt_secret_key_secret_versionless_id
  smtp_password_secret_versionless_id  = module.keyvault.smtp_password_secret_versionless_id

  # Cosmos DB — plain env vars (app uses DefaultAzureCredential, not a connection string)
  cosmos_account_url = module.cosmosdb.account_endpoint
  cosmos_db_name     = module.cosmosdb.db_name

  app_config_endpoint = module.appconfig.endpoint
  key_vault_uri       = module.keyvault.key_vault_uri

  # ACR private registry — UAMI is already granted AcrPull by the acr module
  acr_login_server = module.acr.login_server

  smtp_host            = var.smtp_host
  smtp_port            = var.smtp_port
  smtp_username        = var.smtp_username
  smtp_sender_email    = var.smtp_sender_email
  smtp_use_tls         = var.smtp_use_tls
  smtp_timeout_seconds = var.smtp_timeout_seconds

  tags = local.common_tags
}
