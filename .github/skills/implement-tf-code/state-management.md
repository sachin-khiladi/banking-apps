# State Management

> Sources:
> - [HashiCorp – Remote State](https://developer.hashicorp.com/terraform/language/state/remote)
> - [HashiCorp – `moved` block](https://developer.hashicorp.com/terraform/language/modules/develop/refactoring)
> - [HashiCorp – `import` block](https://developer.hashicorp.com/terraform/language/import)

## Execution Policy (Repository)

- Root-module `terraform plan`/`terraform apply` execution is pipeline-owned.
- Trigger apply only through approved pipeline workflows (manual/on-demand where configured).
- Local CLI examples in this document are for reference semantics and state concepts, not a directive to execute locally.

---

## 1. Remote State Backend (Azure Blob Storage)

Store state in Azure Blob Storage — never commit `.tfstate` files to git.

### Backend configuration (`provider.tf`)

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-tfstate-shared"
    storage_account_name = "stotfstatedev001"      # globally unique
    container_name       = "tfstate"
    key                  = "dev/bankapi.tfstate"    # one key per environment
    use_oidc             = true                     # passwordless CI auth
  }
}
```

### Naming the state key

Use the pattern `<env>/<app>.tfstate` to keep state files clearly separated:

```
tfstate/
├── dev/bankapi.tfstate
├── staging/bankapi.tfstate
└── prod/bankapi.tfstate
```

### Backend storage setup (one-time bootstrap)

The storage account itself should exist before Terraform runs. Provision it with
the Azure CLI or a separate bootstrap Terraform workspace, then commit the backend
config:

```bash
az storage account create \
  --name stotfstatedev001 \
  --resource-group rg-tfstate-shared \
  --sku Standard_LRS \
  --allow-blob-public-access false \
  --min-tls-version TLS1_2

az storage container create \
  --name tfstate \
  --account-name stotfstatedev001 \
  --auth-mode login
```

Enable soft delete and versioning on the container to protect against accidental
state file deletion.

---

## 2. State Locking

The `azurerm` backend uses Azure Blob Storage leases for automatic state locking.
Locking prevents concurrent `apply` operations from corrupting state.

If a lock is stuck after a failed apply, release it explicitly:

```bash
terraform force-unlock <LOCK_ID>
```

> Never run `force-unlock` unless you are certain no other operation is running
> against that state.

---

## 3. Workspaces

Terraform workspaces create isolated state files within the same backend
configuration. Use them sparingly — prefer separate root modules (`environments/dev`,
`environments/prod`) over workspaces for environment isolation, as they are
easier to audit and diff.

When workspaces are appropriate (e.g., feature branch testing):

```bash
terraform workspace new feature-branch-123
terraform workspace select feature-branch-123
terraform plan
```

Reference the workspace name in resource names to avoid collisions:

```hcl
locals {
  env = terraform.workspace == "default" ? var.env : terraform.workspace
}
```

---

## 4. Reading Remote State (Cross-Stack References)

Use `terraform_remote_state` to read outputs from another state file:

```hcl
# Read networking outputs managed by a separate Terraform workspace
data "terraform_remote_state" "networking" {
  backend = "azurerm"

  config = {
    resource_group_name  = "rg-tfstate-shared"
    storage_account_name = "stotfstatedev001"
    container_name       = "tfstate"
    key                  = "${var.env}/networking.tfstate"
  }
}

# Then reference outputs
module "container_app" {
  source    = "../../modules/container_app"
  subnet_id = data.terraform_remote_state.networking.outputs.app_subnet_id
}
```

> Prefer provider data sources (e.g. `data "azurerm_subnet"`) over remote state
> when possible — they are more explicit and do not create cross-state coupling.

---

## 5. Refactoring with `moved` Blocks

When renaming or reorganising resources, use `moved` blocks to preserve state
and avoid destroy/recreate cycles.

### Rename a resource

```hcl
# Before: resource "azurerm_key_vault" "vault"
# After:  resource "azurerm_key_vault" "kv"

moved {
  from = azurerm_key_vault.vault
  to   = azurerm_key_vault.kv
}
```

### Move a resource into a module

```hcl
# Before: resource "azurerm_key_vault" "kv" defined at root
# After:  same resource inside module.keyvault

moved {
  from = azurerm_key_vault.kv
  to   = module.keyvault.azurerm_key_vault.kv
}
```

### Move between `for_each` keys

```hcl
# Before: resource "azurerm_resource_group" "main" (single)
# After:  resource "azurerm_resource_group" "env" for_each = toset(["dev"])

moved {
  from = azurerm_resource_group.main
  to   = azurerm_resource_group.env["dev"]
}
```

**Rules:**
- Add `moved` blocks before running `terraform apply` — not after.
- Remove `moved` blocks only after the state migration has been applied and
  confirmed in all environments.
- Never use CLI `terraform state mv` for changes that can be expressed as
  `moved` blocks — `moved` is version-controlled and reviewable.

---

## 6. Importing Existing Resources

Use the declarative `import` block (Terraform ≥ 1.5) to bring existing Azure
resources under Terraform management without recreation.

### Step 1 — add the `import` block alongside the resource

```hcl
import {
  to = azurerm_resource_group.main
  id = "/subscriptions/<sub-id>/resourceGroups/rg-bankapi-dev"
}

resource "azurerm_resource_group" "main" {
  name     = "rg-bankapi-dev"
  location = "eastus"
  tags     = { environment = "dev", managed_by = "terraform" }
}
```

### Step 2 — generate configuration (if resource block does not exist yet)

```bash
terraform plan -generate-config-out=generated.tf
```

Review `generated.tf`, clean it up to match coding standards, then move the
content into the appropriate `main.tf`.

### Step 3 — apply and verify

```bash
terraform plan    # should show 0 to add, 0 to destroy
terraform apply
```

### Step 4 — remove the `import` block

Once the resource is in state, delete the `import` block. It has no effect on
subsequent runs but adds noise.

---

## 7. Sensitive Values in State

Terraform stores all resource attributes — including sensitive ones — in plain
text in the state file. Mitigations:

1. **Encrypt at rest** — enable Azure Storage encryption (default) and consider
   customer-managed keys for prod.
2. **Restrict access** — use Azure RBAC to limit who can read the storage
   container. Developers should have `Storage Blob Data Reader` at most; the CI
   service principal needs `Storage Blob Data Contributor`.
3. **Never log state** — avoid `terraform show` output in CI logs; pipe through
   `| grep -v sensitive` if needed.
4. **Use Key Vault for secrets** — store secrets in Key Vault and reference them
   via `azurerm_key_vault_secret` data sources at apply time rather than embedding
   them in `tfvars`.

---

## 8. State Operations Quick Reference

| Operation | Command / Approach |
|---|---|
| List all resources in state | `terraform state list` |
| Show a single resource | `terraform state show <address>` |
| Remove a resource from state (without destroying) | `terraform state rm <address>` |
| Rename / reorganise | `moved` block in config |
| Import existing resource | `import` block in config |
| Unlock stuck state | `terraform force-unlock <LOCK_ID>` |
| Pull current state to local file | `terraform state pull > backup.tfstate` |
