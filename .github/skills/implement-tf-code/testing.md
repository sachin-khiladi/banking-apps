# Terraform Testing

> Source: [HashiCorp – Tests](https://developer.hashicorp.com/terraform/language/tests)  
> Requires Terraform ≥ **1.6**. Native test framework replaces third-party tools
> like Terratest for most unit/plan-level tests.

---

## 1. Test File Location & Discovery

Terraform discovers test files by their extension: `.tftest.hcl`

Recommended layout:

```
infra/
└── modules/
    └── keyvault/
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── tests/                 ← test files live here (or same dir)
            ├── unit.tftest.hcl    ← plan-only, no real resources
            └── integration.tftest.hcl  ← apply + assert (needs real Azure)
```

Run all tests from the module directory:

```bash
cd infra/modules/keyvault
terraform test
```

Run only unit (plan) tests (fast, no Azure credentials needed for mock tests):

```bash
terraform test -filter=tests/unit.tftest.hcl
```

---

## 2. Test File Structure

```hcl
# infra/modules/keyvault/tests/unit.tftest.hcl

# File-level variables — shared across all run blocks
variables {
  resource_group_name = "rg-test"
  location            = "eastus"
  app_name            = "bankapi"
  env                 = "dev"
  unique_suffix       = "abc123"
  tenant_id           = "00000000-0000-0000-0000-000000000000"
  deployer_object_id  = "00000000-0000-0000-0000-000000000001"
  tags                = {}
}

# Unit test: validate name length stays within Azure limits
run "kv_name_within_24_chars" {
  command = plan   # no real resources created

  assert {
    condition     = length(azurerm_key_vault.kv.name) <= 24
    error_message = "Key Vault name '${azurerm_key_vault.kv.name}' exceeds 24-character Azure limit."
  }
}

# Unit test: RBAC mode must be enabled
run "kv_rbac_mode_enabled" {
  command = plan

  assert {
    condition     = azurerm_key_vault.kv.enable_rbac_authorization == true
    error_message = "Key Vault must use RBAC authorization mode."
  }
}

# Unit test: dev should have purge_protection disabled
run "dev_purge_protection_off" {
  command = plan

  assert {
    condition     = azurerm_key_vault.kv.purge_protection_enabled == false
    error_message = "purge_protection should be disabled in dev for fast iteration."
  }
}
```

---

## 3. Unit Tests (command = plan)

Unit tests use `command = plan` — Terraform generates a plan without
provisioning real infrastructure. They are safe to run in any environment and
require no Azure credentials when combined with provider mocks.

### Pattern: test naming conventions

```hcl
run "<noun>_<expected_behavior>" {
  command = plan
  assert { ... }
}

# Examples:
run "container_app_name_prefix" { ... }
run "cosmos_serverless_enabled_in_dev" { ... }
run "uami_attached_to_container_app" { ... }
```

### Pattern: validate computed string values

```hcl
run "cosmos_account_name_includes_suffix" {
  command = plan

  assert {
    condition     = endswith(azurerm_cosmosdb_account.cosmos.name, var.unique_suffix)
    error_message = "Cosmos DB account name must end with unique_suffix."
  }
}
```

### Pattern: validate a boolean flag

```hcl
run "cosmosdb_serverless_in_dev" {
  command = plan

  variables {
    enable_serverless = true
  }

  assert {
    condition     = contains(
      [for c in azurerm_cosmosdb_account.cosmos.capabilities : c.name],
      "EnableServerless"
    )
    error_message = "Cosmos serverless capability must be present when enable_serverless = true."
  }
}
```

### Pattern: test a conditional dynamic block is absent when flag is false

```hcl
run "cosmos_serverless_off" {
  command = plan

  variables {
    enable_serverless = false
  }

  assert {
    condition     = !contains(
      [for c in azurerm_cosmosdb_account.cosmos.capabilities : c.name],
      "EnableServerless"
    )
    error_message = "Cosmos serverless capability must not be present when enable_serverless = false."
  }
}
```

---

## 4. Integration Tests (command = apply)

Integration tests provision real Azure resources. Run them in a dedicated
ephemeral test subscription or resource group. They are slower and cost money —
gate them behind a CI environment flag.

```hcl
# tests/integration.tftest.hcl

variables {
  resource_group_name = "rg-tf-test-${run.setup.suffix}"
  location            = "eastus"
  app_name            = "tftest"
  env                 = "dev"
  unique_suffix       = run.setup.suffix
  tenant_id           = run.setup.tenant_id
  deployer_object_id  = run.setup.deployer_oid
  tags                = { managed_by = "terraform-test" }
}

# 1. Create supporting infra (resource group) via a setup module
run "setup" {
  module {
    source = "./tests/setup"
  }
}

# 2. Apply the module under test
run "apply_keyvault" {
  # command = apply is default
  assert {
    condition     = azurerm_key_vault.kv.enable_rbac_authorization == true
    error_message = "Key Vault RBAC must be enabled after apply."
  }

  assert {
    condition     = startswith(azurerm_key_vault.kv.vault_uri, "https://")
    error_message = "Key Vault URI must start with https://."
  }
}
```

---

## 5. Provider Mocks (Terraform ≥ 1.7)

Mocks replace real provider calls so tests run without Azure credentials. Perfect
for pure logic/naming tests in CI.

```hcl
# tests/unit.tftest.hcl

mock_provider "azurerm" {
  mock_resource "azurerm_key_vault" {
    defaults = {
      id                        = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.KeyVault/vaults/kv-test"
      vault_uri                 = "https://kv-test.vault.azure.net/"
      enable_rbac_authorization = true
    }
  }

  mock_resource "azurerm_user_assigned_identity" {
    defaults = {
      id           = "/subscriptions/00000000/resourceGroups/rg-test/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-test"
      principal_id = "00000000-0000-0000-0000-000000000001"
      client_id    = "00000000-0000-0000-0000-000000000002"
    }
  }
}

run "kv_name_format" {
  command = plan   # uses mock provider — no Azure token needed

  assert {
    condition     = startswith(azurerm_key_vault.kv.name, "kv-")
    error_message = "Key Vault name must start with 'kv-'."
  }
}
```

---

## 6. Testing Expected Failures

Use `expect_failures` to verify that invalid inputs are correctly rejected:

```hcl
run "invalid_env_rejected" {
  command = plan

  variables {
    env = "production"   # invalid — not in ["dev", "staging", "prod"]
  }

  expect_failures = [var.env]
}

run "retention_days_too_low" {
  command = plan

  variables {
    kv_soft_delete_retention_days = 3   # below minimum of 7
  }

  expect_failures = [var.kv_soft_delete_retention_days]
}
```

---

## 7. Test Setup Modules

Create reusable setup modules under `tests/setup/` when integration tests
need prerequisite infrastructure (resource groups, subscriptions data, etc.):

```hcl
# tests/setup/main.tf — creates an ephemeral resource group and exposes metadata

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "test" {
  name     = "rg-tftest-${random_id.suffix.hex}"
  location = var.location
  tags     = { managed_by = "terraform-test", ephemeral = "true" }
}

resource "random_id" "suffix" {
  byte_length = 3
}

output "suffix"       { value = random_id.suffix.hex }
output "rg_name"      { value = azurerm_resource_group.test.name }
output "tenant_id"    { value = data.azurerm_client_config.current.tenant_id }
output "deployer_oid" { value = data.azurerm_client_config.current.object_id }
```

---

## 8. What to Test

| Category | Example assertions |
|---|---|
| **Naming** | Resource name matches pattern, length within Azure limits |
| **Tagging** | All required tags present |
| **Security defaults** | RBAC mode on, purge protection in prod, public access off |
| **Dynamic blocks** | Block present/absent based on feature flag |
| **Cross-resource wiring** | UAMI principal_id used in role assignments |
| **Input validation** | Invalid values are rejected (`expect_failures`) |
| **Output contracts** | Outputs are non-empty, match expected format |

---

## 9. CI Integration

Add to your pipeline (see [`pipelines/`](../../../pipelines/)):

```yaml
- name: Terraform Unit Tests
  run: |
    terraform init
    terraform test -filter=tests/unit.tftest.hcl
  working-directory: infra/modules/${{ matrix.module }}
```

Run integration tests only on PRs targeting `main` with a dedicated test
service principal scoped to an isolated test subscription.
