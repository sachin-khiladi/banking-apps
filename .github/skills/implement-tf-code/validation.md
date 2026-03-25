# Validation & Custom Conditions

> Source: [HashiCorp – Validate your configuration](https://developer.hashicorp.com/terraform/language/expressions/custom-conditions)

---

## Overview

Terraform provides four complementary validation mechanisms. Choose the right
one based on *when* you want the check to run and *whether* it should block the
operation.

| Mechanism | Runs at | Blocks operation? | Best for |
|---|---|---|---|
| `variable` `validation` | Plan start (before planning) | ✅ Yes | Checking input values before any API calls |
| `precondition` | Plan phase (before resource creation) | ✅ Yes | Asserting assumptions about data sources / computed values |
| `postcondition` | Apply phase (after resource creation) | ✅ Yes | Asserting guarantees about created resources |
| `check` block | End of plan/apply (non-blocking) | ❌ No (warning) | Monitoring infrastructure health without blocking |

---

## 1. Input Variable Validation

Use `validation` blocks to enforce domain rules on variable values. These run
before any provider API calls.

```hcl
variable "env" {
  type        = string
  description = "Deployment environment (dev | staging | prod)."

  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be one of: dev, staging, prod."
  }
}

variable "kv_soft_delete_retention_days" {
  type        = number
  description = "Days to retain soft-deleted Key Vault secrets (7–90)."
  default     = 7

  validation {
    condition     = var.kv_soft_delete_retention_days >= 7 && var.kv_soft_delete_retention_days <= 90
    error_message = "kv_soft_delete_retention_days must be between 7 and 90."
  }
}

variable "container_image" {
  type        = string
  description = "Full container image reference (registry/repo:tag)."

  validation {
    condition     = can(regex("^[a-z0-9./-]+:[a-zA-Z0-9._-]+$", var.container_image))
    error_message = "container_image must be in the format 'registry/repo:tag'."
  }
}

variable "unique_suffix" {
  type        = string
  description = "6-character suffix for globally unique resource names."

  validation {
    condition     = length(var.unique_suffix) == 6
    error_message = "unique_suffix must be exactly 6 characters."
  }
}
```

### Multiple conditions on one variable

Chain multiple rules with `&&`:

```hcl
variable "log_retention_days" {
  type        = number
  description = "Log Analytics workspace data retention period in days."
  default     = 30

  validation {
    condition     = var.log_retention_days >= 30 && var.log_retention_days <= 730
    error_message = "log_retention_days must be between 30 and 730."
  }
}
```

Or use separate `validation` blocks for distinct rules with separate messages:

```hcl
variable "app_name" {
  type        = string
  description = "Short application identifier used in resource names."

  validation {
    condition     = length(var.app_name) <= 12
    error_message = "app_name must be 12 characters or fewer to fit in resource name length limits."
  }

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.app_name))
    error_message = "app_name must start with a letter and contain only lowercase letters, digits, and hyphens."
  }
}
```

---

## 2. Preconditions

Preconditions evaluate **after** the plan is built but **before** a resource is
created. Use them to guard against misconfigured data sources or computed values
being passed into resources.

```hcl
# Guard: the CAE must be in the same region as the resource group
resource "azurerm_container_app" "app" {
  container_app_environment_id = azurerm_container_app_environment.cae.id

  lifecycle {
    precondition {
      condition     = var.location == azurerm_container_app_environment.cae.location
      error_message = "Container App and its Environment must be in the same Azure region."
    }
  }
}
```

```hcl
# Guard: Cosmos DB serverless cannot be combined with multi-region writes
resource "azurerm_cosmosdb_account" "cosmos" {
  lifecycle {
    precondition {
      condition     = !(var.enable_serverless && var.enable_multi_master)
      error_message = "Cosmos DB serverless capacity mode is incompatible with multi-master writes."
    }
  }
}
```

```hcl
# Guard on an output — verify a module output meets contract before exposing it
output "kv_uri" {
  description = "Key Vault URI."
  value       = azurerm_key_vault.kv.vault_uri

  precondition {
    condition     = startswith(azurerm_key_vault.kv.vault_uri, "https://")
    error_message = "Key Vault URI must begin with https://."
  }
}
```

---

## 3. Postconditions

Postconditions evaluate **after** a resource or data source is created/read.
Use them to assert guarantees about the actual deployed state.

```hcl
# Verify the ACR SKU is Premium before enabling private endpoints
resource "azurerm_container_registry" "acr" {
  lifecycle {
    postcondition {
      condition     = self.sku == "Premium" || !var.enable_private_endpoint
      error_message = "Private endpoint for ACR requires Premium SKU."
    }
  }
}
```

```hcl
# data source postcondition — assert the looked-up subnet exists in the right VNet
data "azurerm_subnet" "app" {
  lifecycle {
    postcondition {
      condition     = self.virtual_network_name == var.vnet_name
      error_message = "Subnet '${self.name}' does not belong to VNet '${var.vnet_name}'."
    }
  }
}
```

### When to pick precondition vs postcondition

| Situation | Use |
|---|---|
| Checking a caller-supplied value before any resource is created | `variable` validation or `precondition` |
| Checking a data source attribute read back from Azure | `precondition` (plan phase) or `postcondition` |
| Checking a resource attribute that only exists after `apply` | `postcondition` |
| Catching configuration drift in long-running infra | `check` block |

---

## 4. `check` Blocks

`check` blocks run as the **last** step of every plan/apply and emit a **warning**
(never an error). Use them for non-critical assertions and infrastructure health
monitoring.

```hcl
# Assert App Insights returns a live probe
check "app_insights_live" {
  data "http" "health" {
    url = "https://${azurerm_container_app.app.latest_revision_fqdn}/health"
  }

  assert {
    condition     = data.http.health.status_code == 200
    error_message = "Container App health endpoint returned ${data.http.health.status_code}."
  }
}
```

```hcl
# Assert Cosmos DB public access is intentionally disabled in prod
check "cosmos_public_access" {
  assert {
    condition     = var.env != "prod" || !azurerm_cosmosdb_account.cosmos.public_network_access_enabled
    error_message = "Cosmos DB public network access should be disabled in prod."
  }
}
```

> Note: `check` blocks never stop a `plan` or `apply` — they are informational
> guards. Use `precondition` / `postcondition` when the operation must stop on
> failure.

---

## 5. Helpful Validation Functions

| Function | Purpose |
|---|---|
| `contains(list, val)` | Enum membership check |
| `can(expr)` | Returns true if expression doesn't throw an error (useful with `regex`) |
| `length(val)` | String/list/map length |
| `startswith(str, prefix)` | Prefix check (Terraform ≥ 1.3) |
| `endswith(str, suffix)` | Suffix check (Terraform ≥ 1.3) |
| `regex(pattern, str)` | Pattern match (throws if no match; wrap in `can()`) |
| `tonumber(val)` | Type coercion with implicit error on failure |

---

## 6. Validation Error Message Guidelines

- Write in full sentences, like Terraform's own error messages.
- Reference the variable name and current value when helpful:

```hcl
validation {
  condition     = var.min_replicas <= var.max_replicas
  error_message = "min_replicas (${var.min_replicas}) must be less than or equal to max_replicas (${var.max_replicas})."
}
```

- Keep messages under two sentences — long messages are truncated in some CI UIs.
