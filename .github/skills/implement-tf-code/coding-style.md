# Coding Style

> Source: [HashiCorp Terraform Style Guide](https://developer.hashicorp.com/terraform/language/style)

---

## 1. Formatting

Run **`terraform fmt -recursive`** before every commit. Never hand-format spacing
— let the tool own it.

### Layout rules (enforced by `terraform fmt`)

| Rule | Example |
|---|---|
| 2-space indent per nesting level | ✅ `  resource "..."` |
| Align `=` signs on consecutive single-value arguments | ✅ `name = "foo"` / `location = "eastus"` |
| One blank line between top-level blocks | ✅ resource ↔ resource |
| Meta-arguments (`count`, `for_each`, `depends_on`, `lifecycle`) at top of block, separated by a blank line from other args | ✅ |
| `lifecycle` block last in a resource block | ✅ |

```hcl
# Good
resource "azurerm_resource_group" "main" {
  # meta-argument first
  for_each = var.environments

  name     = "rg-${each.key}"
  location = var.location
  tags     = var.tags

  lifecycle {
    prevent_destroy = true
  }
}
```

---

## 2. Validation Before Committing

```bash
# format check (CI-safe, non-mutating)
terraform fmt -check -recursive

# structural & type correctness (no provider calls)
terraform validate
```

Use **TFLint** for provider-aware linting in CI:

```bash
tflint --init
tflint --recursive
```

Recommended TFLint rule sets for this repo:
- `terraform` (built-in)
- `tflint-ruleset-azurerm` — catches deprecated/invalid `azurerm` arguments

---

## 3. File Names

Following the [HashiCorp convention](https://developer.hashicorp.com/terraform/language/style#file-names):

| File | Purpose |
|---|---|
| `main.tf` | Resources and data sources (primary entrypoint) |
| `variables.tf` | All `variable` blocks, alphabetical order |
| `outputs.tf` | All `output` blocks, alphabetical order |
| `provider.tf` | `terraform {}` + `provider {}` blocks |
| `locals.tf` | `locals {}` blocks referenced across files |
| `versions.tf` | (alternative to `provider.tf`) version pins only |

> For large root modules, split into logical files:
> `network.tf`, `identity.tf`, `monitoring.tf`, etc.

---

## 4. Comments

Use `#` for all comments (not `//` or `/* */`).

```hcl
# ---------------------------------------------------------------------------
# Section header (helps navigation in large files)
# ---------------------------------------------------------------------------

# Inline reason — explain *why*, not what
resource "azurerm_key_vault" "kv" {
  enable_rbac_authorization = true  # RBAC mode; no legacy access policies
}
```

Section dividers (`# ---`) are encouraged in files > 100 lines.

---

## 5. Naming Conventions

| Construct | Pattern | Example |
|---|---|---|
| Resources / data sources | `snake_case` noun, no type redundancy | `"main"`, `"app_identity"` |
| Variables | `snake_case` noun | `resource_group_name` |
| Outputs | `snake_case` noun, descriptive | `cosmos_account_url` |
| Local values | `snake_case` noun | `unique_suffix`, `common_tags` |
| Module calls | `snake_case` noun matching the module name | `module "keyvault"` |

**Do not** include the resource type in the resource label:

```hcl
# Bad
resource "azurerm_resource_group" "resource_group_main" { ... }

# Good
resource "azurerm_resource_group" "main" { ... }
```

---

## 6. Resource Ordering Within a File

Define data sources before the resources that consume them — code should "build
on itself":

```hcl
data "azurerm_client_config" "current" {}

locals {
  deployer_object_id = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "kv_admin" {
  principal_id = local.deployer_object_id
  ...
}
```

---

## 7. Variables

Required parameter order inside every `variable` block:

1. `type`
2. `description`
3. `default` (optional)
4. `sensitive` (optional)
5. `validation` blocks (optional)

```hcl
variable "env" {
  type        = string
  description = "Deployment environment identifier (dev | staging | prod)."

  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be one of: dev, staging, prod."
  }
}

variable "kv_soft_delete_retention_days" {
  type        = number
  description = "Number of days Key Vault secrets are retained after soft-delete."
  default     = 7
}

variable "cosmos_primary_key" {
  type        = string
  description = "Cosmos DB primary key — injected from Key Vault at plan time."
  sensitive   = true
}
```

Rules:
- Every variable **must** have `type` and `description`.
- Use `validation` blocks for inputs with restricted domains (enums, ranges, patterns).
- Mark secrets `sensitive = true` to suppress output in `plan`/`apply` logs.

---

## 8. Outputs

Required parameter order inside every `output` block:

1. `description`
2. `value`
3. `sensitive` (optional)

```hcl
output "cosmos_account_url" {
  description = "Cosmos DB SQL endpoint for the application container."
  value       = azurerm_cosmosdb_account.cosmos.endpoint
}

output "kv_uri" {
  description = "URI of the Key Vault instance."
  value       = azurerm_key_vault.kv.vault_uri
}
```

---

## 9. Local Values

Use `locals` to eliminate repetition and name intermediate computations:

```hcl
locals {
  app_name      = "bankapi"
  unique_suffix = substr(data.azurerm_client_config.current.subscription_id, 27, 6)
  name_prefix   = "${local.app_name}-${var.env}"

  common_tags = {
    environment = var.env
    application = local.app_name
    managed_by  = "terraform"
  }
}
```

Keep `locals` in `locals.tf` when referenced across multiple files; inline at the
top of a file when file-specific.

---

## 10. `count` vs `for_each`

| Use | When |
|---|---|
| `count = N` | Identical resources differentiated only by index |
| `count = condition ? 1 : 0` | Conditional single resource |
| `for_each = map/set` | Resources with distinct configuration per element |

Prefer `for_each` over `count` for collections — it produces stable addresses
when items are added or removed:

```hcl
# Stable: removing "staging" does not affect "prod"
resource "azurerm_resource_group" "env" {
  for_each = toset(["dev", "staging", "prod"])
  name     = "rg-bankapi-${each.key}"
  location = var.location
}
```

---

## 11. `dynamic` Blocks

Use `dynamic` only when a nested block is genuinely optional or variable in
count. Add a comment explaining the condition:

```hcl
# ACR registry pull — only wired when the image comes from a private ACR.
# Set acr_login_server = null to skip (e.g. public MCR images).
dynamic "registry" {
  for_each = var.acr_login_server != null ? [1] : []
  content {
    server   = var.acr_login_server
    identity = var.uami_id
  }
}
```

---

## 12. Version Pinning

Always pin provider versions. Use `~>` to allow patch-level upgrades but lock
the major/minor:

```hcl
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
```

Commit the `.terraform.lock.hcl` file — it records the exact provider checksums
selected at `terraform init`.

---

## 13. `.gitignore` Checklist

Never commit:

```gitignore
.terraform/
*.tfstate
*.tfstate.*
*.tfstate.backup
.terraform.tfstate.lock.info
*.tfplan
*.tfvars          # if they contain secrets
override.tf
override.tf.json
*_override.tf
*_override.tf.json
```

Always commit: `*.tf`, `.terraform.lock.hcl`, `terraform.tfvars.example`.
