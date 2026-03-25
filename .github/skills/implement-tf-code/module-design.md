# Module Design

> Source: [HashiCorp Standard Module Structure](https://developer.hashicorp.com/terraform/language/modules/develop/structure)
> and [Module Composition](https://developer.hashicorp.com/terraform/language/modules/develop/composition)

---

## 1. Repository Layout (This Project)

```
infra/
├── environments/
│   ├── dev/                  ← Root module (environment entrypoint)
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── provider.tf
│   │   └── terraform.tfvars
│   └── prod/
│       └── ...               ← Mirror of dev with prod values
└── modules/                  ← Reusable child modules
    ├── acr/
    ├── appconfig/
    ├── container_app/
    ├── cosmosdb/
    ├── keyvault/
    └── monitoring/
```

Every child module under `modules/` must contain exactly:

| File | Required | Purpose |
|---|---|---|
| `main.tf` | ✅ | Resource definitions |
| `variables.tf` | ✅ | Input declarations |
| `outputs.tf` | ✅ | Output declarations |
| `README.md` | ✅ | Module description, inputs, outputs table |

---

## 2. Root Module Responsibilities

The root module (`environments/<env>/main.tf`) **wires** child modules together.
It must **not** define leaf resources directly — delegate to child modules.

```hcl
# environments/dev/main.tf — correct: only module calls + locals + data sources

data "azurerm_client_config" "current" {}

locals {
  app_name      = "bankapi"
  unique_suffix = substr(data.azurerm_client_config.current.subscription_id, 27, 6)
  common_tags   = { environment = var.env, managed_by = "terraform" }
}

resource "azurerm_resource_group" "main" {
  # The root RG is legitimately defined here — it's the anchor for all modules.
  name     = "rg-${local.app_name}-${var.env}"
  location = var.location
  tags     = local.common_tags
}

module "monitoring" {
  source              = "../../modules/monitoring"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  app_name            = local.app_name
  env                 = var.env
  tags                = local.common_tags
}

module "keyvault" {
  source              = "../../modules/keyvault"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  app_name            = local.app_name
  env                 = var.env
  unique_suffix       = local.unique_suffix
  tenant_id           = data.azurerm_client_config.current.tenant_id
  deployer_object_id  = data.azurerm_client_config.current.object_id
  tags                = local.common_tags
}
```

---

## 3. Child Module Design Contract

### 3.1 Single Responsibility

Each module provisions one logical concern:

| Module | Concern |
|---|---|
| `monitoring` | Log Analytics Workspace + Application Insights |
| `keyvault` | Key Vault + UAMI + RBAC + Secrets |
| `cosmosdb` | Cosmos Account + Database + Container + RBAC |
| `container_app` | Container App Environment + Container App |
| `acr` | Azure Container Registry + ACR Pull RBAC |

### 3.2 Input Variables Pattern

```hcl
# variables.tf — standard inputs every module should declare

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group that hosts this module's resources."
}

variable "location" {
  type        = string
  description = "Azure region for all resources in this module."
}

variable "app_name" {
  type        = string
  description = "Short application name used as a naming prefix."
}

variable "env" {
  type        = string
  description = "Environment identifier (dev | staging | prod)."

  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be one of: dev, staging, prod."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to all resources in this module."
  default     = {}
}
```

### 3.3 Output Variables Pattern

Expose only what callers need. Never expose sensitive values unless `sensitive = true`.

```hcl
# outputs.tf

output "id" {
  description = "Resource ID of the primary resource in this module."
  value       = azurerm_key_vault.kv.id
}

output "uri" {
  description = "HTTPS URI of the Key Vault."
  value       = azurerm_key_vault.kv.vault_uri
}

output "uami_id" {
  description = "Resource ID of the User-Assigned Managed Identity."
  value       = azurerm_user_assigned_identity.app_identity.id
}

output "uami_principal_id" {
  description = "Object (principal) ID of the UAMI — used for RBAC assignments."
  value       = azurerm_user_assigned_identity.app_identity.principal_id
}
```

---

## 4. Module Composition (Passing Outputs Between Modules)

Connect modules through root module wiring — child modules must **never** call
each other directly:

```hcl
# environments/dev/main.tf

module "keyvault" {
  source             = "../../modules/keyvault"
  # ... standard vars ...
  app_insights_connection_string = module.monitoring.app_insights_connection_string
}

module "container_app" {
  source  = "../../modules/container_app"
  # pass outputs from other modules as inputs
  uami_id                           = module.keyvault.uami_id
  log_analytics_workspace_id        = module.monitoring.log_analytics_workspace_id
  cosmos_account_url                = module.cosmosdb.account_url
  appinsights_secret_versionless_id = module.keyvault.appinsights_secret_versionless_id
  acr_login_server                  = module.acr.login_server
}
```

This keeps the dependency graph explicit and testable at the root level.

---

## 5. Naming Resources Inside a Module

Compose names from module inputs — never hard-code environment or app name:

```hcl
resource "azurerm_key_vault" "kv" {
  # max 24 chars; suffix ensures global uniqueness
  name = "kv-${var.app_name}-${var.env}-${var.unique_suffix}"
  ...
}
```

Standard nameprefix convention used in this project:

| Resource type | Pattern |
|---|---|
| Resource Group | `rg-<app>-<env>` |
| Key Vault | `kv-<app>-<env>-<suffix>` |
| Container App | `ca-<app>-<env>` |
| Container App Env | `cae-<app>-<env>` |
| Cosmos Account | `cosmos-<app>-<env>-<suffix>` |
| Log Analytics | `log-<app>-<env>` |
| App Insights | `appi-<app>-<env>` |
| User-Assigned MI | `id-<app>-<env>` |
| ACR | `acr<app><env><suffix>` (alphanumeric only) |

---

## 6. `depends_on` — Explicit vs Implicit

Prefer implicit dependencies through resource references. Only use `depends_on`
when Terraform cannot infer a real ordering dependency:

```hcl
# Implicit (preferred) — Terraform infers the dependency
resource "azurerm_container_app" "app" {
  container_app_environment_id = azurerm_container_app_environment.cae.id
  # ↑ Terraform already knows to create the CAE first
}

# Explicit — only when needed (e.g., role assignment must exist before app starts)
resource "azurerm_container_app" "app" {
  depends_on = [azurerm_role_assignment.acr_pull_uami]
}
```

---

## 7. `lifecycle` Meta-argument Patterns

```hcl
# Prevent accidental destruction of stateful resources in prod
resource "azurerm_cosmosdb_account" "cosmos" {
  lifecycle {
    prevent_destroy = true  # set only in prod module; keep false in dev
  }
}

# Ignore changes to tags managed outside Terraform (e.g. by Azure Policy)
resource "azurerm_resource_group" "main" {
  lifecycle {
    ignore_changes = [tags["auto-managed-by-policy"]]
  }
}

# Replace image without destroy (blue/green)
resource "azurerm_container_app" "app" {
  lifecycle {
    create_before_destroy = true
  }
}
```

---

## 8. Module README Template

Every module must have a `README.md` with this structure:

```markdown
# Module: <module_name>

Brief description of what this module provisions.

## Resources Created

- `azurerm_X` — purpose
- `azurerm_Y` — purpose

## Usage

```hcl
module "<name>" {
  source = "../../modules/<module_name>"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  app_name            = local.app_name
  env                 = var.env
  tags                = local.common_tags
}
```

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| resource_group_name | string | ✅ | ... |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| id   | string | Resource ID of the primary resource |
```

---

## 9. Anti-Patterns to Avoid

| Anti-pattern | Correct approach |
|---|---|
| Hard-coding environment names or regions inside a module | Pass them as variables |
| Calling one child module from another child module | Wire through root module |
| Defining providers inside a child module | Define providers only in root module |
| Using `terraform_remote_state` inside a child module | Pass required values as variables |
| Outputting secrets without `sensitive = true` | Always mark secret outputs sensitive |
