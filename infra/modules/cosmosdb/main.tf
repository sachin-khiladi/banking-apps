# ===========================================================================
# Module: cosmosdb
# Provisions: Cosmos DB Account (SQL/NoSQL API) + Database + Container + RBAC
#
# Networking philosophy:
#   public_network_access_enabled = true, no VNet filter → every public IP
#   (your local workstation, Azure Container Apps, CI pipelines) can reach
#   the data plane without extra firewall rules.  Restrict further in prod
#   by adding an ip_range_filter variable if needed.
# ===========================================================================

resource "azurerm_cosmosdb_account" "cosmos" {
  name                = "cosmos-${var.app_name}-${var.env}-${var.unique_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  # ── Networking ─────────────────────────────────────────────────────────────
  # Explicitly allow all public IPs (local workstation + Azure services).
  # No VNet integration — simplest setup for dev; tighten for prod if needed.
  public_network_access_enabled     = true
  is_virtual_network_filter_enabled = false

  # ── Consistency ────────────────────────────────────────────────────────────
  consistency_policy {
    consistency_level = var.consistency_level
  }

  # ── Geo-location (single primary region) ───────────────────────────────────
  # zone_redundant = false is explicit — prevents the AzureRM provider from
  # requesting zonal-redundant capacity, which is constrained in East US.
  geo_location {
    location          = var.location
    failover_priority = 0
    zone_redundant    = false
  }

  # ── Serverless capability ─────────────────────────────────────────────────
  # Enable for dev (no per-RU provisioned cost).
  # Omit (enable_serverless = false) for prod to use autoscale provisioned RUs.
  dynamic "capabilities" {
    for_each = var.enable_serverless ? [1] : []
    content {
      name = "EnableServerless"
    }
  }

  tags = var.tags

  lifecycle {
    precondition {
      condition     = !(var.env == "prod" && var.enable_serverless)
      error_message = "Production Cosmos DB deployments must use provisioned throughput; set enable_serverless = false."
    }
  }
}

# ── SQL Database ──────────────────────────────────────────────────────────────

resource "azurerm_cosmosdb_sql_database" "db" {
  name                = var.db_name
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.cosmos.name
}

# ── SQL Container ─────────────────────────────────────────────────────────────
# Partition key matches the app constant: _PARTITION_KEY = "accountNumber"

resource "azurerm_cosmosdb_sql_container" "accounts" {
  name                  = var.container_name
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.cosmos.name
  database_name         = azurerm_cosmosdb_sql_database.db.name
  partition_key_paths   = [var.partition_key_path]
  partition_key_version = 2

  # Autoscale throughput only applies in provisioned mode.
  # In serverless mode this block must be absent.
  dynamic "autoscale_settings" {
    for_each = var.enable_serverless ? [] : [1]
    content {
      max_throughput = var.max_throughput
    }
  }

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }

    excluded_path {
      path = "/\"_etag\"/?"
    }
  }
}

# ── SQL Container: user_profiles ────────────────────────────────────────────────
# Partition key matches the app field: owner_id

resource "azurerm_cosmosdb_sql_container" "user_profiles" {
  name                  = "user_profiles"
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.cosmos.name
  database_name         = azurerm_cosmosdb_sql_database.db.name
  partition_key_paths   = ["/owner_id"]
  partition_key_version = 2

  # Autoscale throughput only applies in provisioned mode.
  # In serverless mode this block must be absent.
  dynamic "autoscale_settings" {
    for_each = var.enable_serverless ? [] : [1]
    content {
      max_throughput = var.max_throughput
    }
  }

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }

    excluded_path {
      path = "/\"_etag\"/?"
    }
  }
}

# ── RBAC: deployer → Cosmos DB Built-in Data Contributor ─────────────────────
# Grants the principal running Terraform (your local machine / CI pipeline)
# full data-plane read/write access so you can query Cosmos from your
# workstation using az CLI or the Azure Portal Data Explorer.

resource "azurerm_cosmosdb_sql_role_assignment" "deployer_data_contributor" {
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.cosmos.name

  # Built-in role: 00000000-0000-0000-0000-000000000002 = Data Contributor
  role_definition_id = "${azurerm_cosmosdb_account.cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id       = var.deployer_object_id
  scope              = azurerm_cosmosdb_account.cosmos.id

  lifecycle {
    ignore_changes = [role_definition_id]
  }
}

resource "azurerm_cosmosdb_sql_role_assignment" "app_data_contributor" {
  count = var.assign_app_cosmosdb_role ? 1 : 0

  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.cosmos.name

  # Built-in role: 00000000-0000-0000-0000-000000000002 = Data Contributor
  role_definition_id = "${azurerm_cosmosdb_account.cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id       = var.app_uami_principal_id
  scope              = azurerm_cosmosdb_account.cosmos.id

  lifecycle {
    ignore_changes = [role_definition_id]
  }
}
