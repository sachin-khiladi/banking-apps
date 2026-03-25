# Azure Provider Patterns

> Source: [azurerm provider documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)  
> Patterns derived from this repository's modules (`infra/modules/`).

---

## 1. Provider & Version Configuration

```hcl
# infra/environments/dev/provider.tf

terraform {
  required_version = ">= 1.6"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.47"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false   # keep soft-deleted items in dev
      recover_soft_deleted_key_vaults = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false  # allow clean dev teardown
    }
  }
}
```

- Always specify `features {}` block — it is required even if empty.
- Tune `key_vault.purge_soft_delete_on_destroy` per environment in `terraform.tfvars`.
- Never define providers inside child modules.

---

## 2. Identity — User-Assigned Managed Identity (UAMI)

Use UAMI (not system-assigned) for applications so the identity can be assigned
role bindings before the resource that uses it is created, avoiding circular
dependencies.

```hcl
# modules/keyvault/main.tf

resource "azurerm_user_assigned_identity" "app_identity" {
  name                = "id-${var.app_name}-${var.env}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}
```

Reference in Container App:

```hcl
# modules/container_app/main.tf

resource "azurerm_container_app" "app" {
  identity {
    type         = "UserAssigned"
    identity_ids = [var.uami_id]
  }
}
```

Export from the keyvault module, import into container_app module via the root:

```hcl
# environments/dev/main.tf
module "container_app" {
  uami_id = module.keyvault.uami_id
}
```

---

## 3. RBAC — Role Assignments Pattern

Always use role-based access control (not legacy access policies). Assign the
minimum required role at the narrowest scope.

### Deployer gets admin role to write secrets

```hcl
resource "azurerm_role_assignment" "kv_admin_deployer" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = var.deployer_object_id
}
```

### UAMI gets read-only role at runtime

```hcl
resource "azurerm_role_assignment" "kv_secrets_user_app" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.app_identity.principal_id
}
```

### ACR pull for Container App UAMI

```hcl
resource "azurerm_role_assignment" "acr_pull_uami" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = var.uami_principal_id
}
```

### Common built-in role names for this project

| Scope | Role | Principal |
|---|---|---|
| Key Vault | `Key Vault Administrator` | CI deployer service principal |
| Key Vault | `Key Vault Secrets User` | Container App UAMI |
| ACR | `AcrPull` | Container App UAMI |
| Cosmos DB | `Cosmos DB Built-in Data Contributor` | Container App UAMI |
| App Configuration | `App Configuration Data Reader` | Container App UAMI |
| Storage | `Storage Blob Data Contributor` | CI deployer (state backend) |

---

## 4. Key Vault Secrets — No Plaintext in State

Store secrets in Key Vault and reference by versionless URI in Container Apps.
This keeps the secret value out of the Container App revision spec and out of
state.

```hcl
# modules/keyvault/main.tf — write secret once
resource "azurerm_key_vault_secret" "appinsights_connection_string" {
  name         = "appinsights-connection-string"
  value        = var.app_insights_connection_string
  key_vault_id = azurerm_key_vault.kv.id
  depends_on   = [azurerm_role_assignment.kv_admin_deployer]
}

# Output the versionless URI so no specific version is pinned
output "appinsights_secret_versionless_id" {
  description = "Versionless Key Vault URI for the App Insights secret."
  value       = "${azurerm_key_vault.kv.vault_uri}secrets/${azurerm_key_vault_secret.appinsights_connection_string.name}"
}
```

```hcl
# modules/container_app/main.tf — reference secret by URI, not value
secret {
  name                = "appinsights-connection-string"
  key_vault_secret_id = var.appinsights_secret_versionless_id
  identity            = var.uami_id
}

template {
  container {
    env {
      name        = "APPLICATIONINSIGHTS_CONNECTION_STRING"
      secret_name = "appinsights-connection-string"
    }
  }
}
```

---

## 5. Cosmos DB SQL API Patterns

```hcl
resource "azurerm_cosmosdb_account" "cosmos" {
  name                = "cosmos-${var.app_name}-${var.env}-${var.unique_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"   # SQL / NoSQL API

  public_network_access_enabled     = var.env == "prod" ? false : true
  is_virtual_network_filter_enabled = false

  consistency_policy {
    consistency_level = var.consistency_level   # "Session" is a safe default
  }

  geo_location {
    location          = var.location
    failover_priority = 0
    zone_redundant    = false   # set true in prod if needed
  }

  # Conditional serverless — dev only
  dynamic "capabilities" {
    for_each = var.enable_serverless ? [1] : []
    content {
      name = "EnableServerless"
    }
  }

  tags = var.tags
}
```

### Cosmos DB RBAC (passwordless)

Grant the UAMI data-plane access via built-in role instead of connection strings:

```hcl
resource "azurerm_cosmosdb_sql_role_assignment" "app_data_contributor" {
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.cosmos.name
  role_definition_id  = "${azurerm_cosmosdb_account.cosmos.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = var.uami_principal_id
  scope               = azurerm_cosmosdb_account.cosmos.id
}
```

Role ID `...0002` = **Cosmos DB Built-in Data Contributor** (read + write).
Role ID `...0001` = **Cosmos DB Built-in Data Reader** (read-only).

---

## 6. Azure Container Apps

### Container App Environment

```hcl
resource "azurerm_container_app_environment" "cae" {
  name                       = "cae-${var.app_name}-${var.env}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id
  tags                       = var.tags
}
```

### Container App with dynamic ACR registry block

```hcl
resource "azurerm_container_app" "app" {
  name                         = "ca-${var.app_name}-${var.env}"
  container_app_environment_id = azurerm_container_app_environment.cae.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [var.uami_id]
  }

  # Optional — wired only when using a private ACR
  dynamic "registry" {
    for_each = var.acr_login_server != null ? [1] : []
    content {
      server   = var.acr_login_server
      identity = var.uami_id
    }
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = var.app_name
      image  = var.container_image
      cpu    = var.container_cpu    # e.g. 0.5
      memory = var.container_memory # e.g. "1Gi"
    }
  }
}
```

### Variable defaults for Container App sizing

```hcl
variable "min_replicas"       { type = number; default = 1 }
variable "max_replicas"       { type = number; default = 3 }
variable "container_cpu"      { type = number; default = 0.5 }
variable "container_memory"   { type = string; default = "1Gi" }
variable "acr_login_server"   { type = string; default = null }
```

---

## 7. Azure Container Registry (ACR)

```hcl
resource "azurerm_container_registry" "acr" {
  # ACR names: alphanumeric only, 5–50 chars
  name                = "acr${var.app_name}${var.env}${var.unique_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.acr_sku   # "Basic" for dev, "Standard" for prod

  admin_enabled = false   # use UAMI + AcrPull role; never enable admin

  tags = var.tags
}

output "login_server" {
  description = "FQDN of the ACR login server."
  value       = azurerm_container_registry.acr.login_server
}
```

---

## 8. Monitoring — Log Analytics + Application Insights

```hcl
resource "azurerm_log_analytics_workspace" "law" {
  name                = "log-${var.app_name}-${var.env}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days   # 30 dev, 90+ prod
  tags                = var.tags
}

resource "azurerm_application_insights" "appi" {
  name                = "appi-${var.app_name}-${var.env}"
  resource_group_name = var.resource_group_name
  location            = var.location
  workspace_id        = azurerm_log_analytics_workspace.law.id
  application_type    = "web"
  tags                = var.tags
}

output "app_insights_connection_string" {
  description = "Application Insights connection string for SDK initialisation."
  value       = azurerm_application_insights.appi.connection_string
  sensitive   = true
}
```

---

## 9. Azure App Configuration

```hcl
resource "azurerm_app_configuration" "appconfig" {
  name                = "appcs-${var.app_name}-${var.env}-${var.unique_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.appconfig_sku   # "free" dev, "standard" prod
  tags                = var.tags
}

resource "azurerm_role_assignment" "appconfig_reader_uami" {
  scope                = azurerm_app_configuration.appconfig.id
  role_definition_name = "App Configuration Data Reader"
  principal_id         = var.uami_principal_id
}
```

---

## 10. `data.azurerm_client_config` Pattern

Use `data.azurerm_client_config.current` to obtain the deployer's identity at
plan time — avoids hard-coding subscription IDs or object IDs in `tfvars`:

```hcl
data "azurerm_client_config" "current" {}

locals {
  unique_suffix      = substr(data.azurerm_client_config.current.subscription_id, 27, 6)
  deployer_object_id = data.azurerm_client_config.current.object_id
  tenant_id          = data.azurerm_client_config.current.tenant_id
}
```

---

## 11. Common `azurerm` Gotchas

| Gotcha | Fix |
|---|---|
| Key Vault name > 24 chars | Use `substr(...)` suffix from subscription ID |
| ACR name must be alphanumeric | Strip hyphens: `replace("acr-${var.app_name}", "-", "")` |
| `azurerm_role_assignment` needs RBAC on provider | Add `skip_service_principal_aad_check = true` for service principals |
| Container App revision not updating | Change `revision_mode = "Multiple"` or force update via env var bump |
| Cosmos DB serverless + provisioned throughput conflict | Use `dynamic "capabilities"` with `for_each = var.enable_serverless ? [1] : []` |
| Soft-deleted Key Vault blocks recreation | Set `recover_soft_deleted_key_vaults = true` in provider `features` block |
| RBAC propagation lag | Add `depends_on` on resources that rely on role assignments being active |

---

## 12. Tagging Convention

All resources must include a `tags` variable passed from the root module:

```hcl
locals {
  common_tags = {
    environment = var.env          # dev | staging | prod
    application = local.app_name   # bankapi
    managed_by  = "terraform"
    owner       = "platform-team"
  }
}
```

Pass `tags = local.common_tags` to every module. Each module passes `tags` to
every resource it creates. Never hard-code tags inside modules.
