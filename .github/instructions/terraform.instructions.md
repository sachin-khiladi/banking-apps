---
applyTo: "infra/**/*.tf"
---

# Terraform Coding Standards

> **Agent instruction**: Before writing or editing ANY Terraform file, read `.github/skills/implement-tf-code/SKILL.md` and the relevant sub-documents. This file is the trigger — the skill file is the authoritative guide.

## Mandatory Pre-Work

1. Read `.github/skills/implement-tf-code/SKILL.md`
2. Based on the task, read the applicable sub-documents:
   - Editing style/naming → `coding-style.md`
   - New module or restructuring → `module-design.md`
   - Adding variables with rules → `validation.md`
   - Writing `.tftest.hcl` → `testing.md`
   - State operations (`mv`, `import`, workspaces) → `state-management.md`
   - Any `azurerm` resource → `azure-patterns.md`

## Quick Rules (never deviate without skill file authorisation)

- Target Terraform ≥ **1.6**, `azurerm` ≥ **3.x**
- All Azure resources: User-Assigned Managed Identity (UAMI), never system-assigned for new resources
- Required tags block on every resource: `environment`, `owner`, `cost-center`
- Remote state in Azure Blob Storage — never local state in CI/CD
- Terraform `plan`/`apply` for environment root modules must run via pipeline workflows only (manual or policy trigger). Do not run local `terraform apply` from a developer workstation.
- Never commit Terraform local runtime artifacts (`.terraform/`, `terraform.tfstate*`, `tfplan*`, `crash.log`, `override.tf*`, `*_override.tf*`)
- One module per Azure service (`container_app`, `cosmosdb`, `keyvault`, etc.)
- Module inputs: typed with descriptions and validation blocks
- Outputs: expose only what callers need — never expose secrets as plaintext outputs
- `terraform fmt` and `terraform validate` must pass before committing
- `terraform plan` (no apply) must produce zero errors before concluding any change — run locally using a `backend_override.tf` with `backend "local" {}` and delete it before committing

## Pre-Commit Validation Gate

Every change to `infra/` **must** complete all three checks with zero errors before the change is considered done:

```bash
# 1. Format — all changed modules and environments
terraform -chdir=infra/modules/<module>    fmt -check -diff
terraform -chdir=infra/environments/dev    fmt -check -diff
terraform -chdir=infra/environments/prod   fmt -check -diff

# 2. Validate — run against dev environment
#    Create infra/environments/dev/backend_override.tf with backend "local" {},
#    then delete it after validation. Never commit this file.
terraform -chdir=infra/environments/dev init -reconfigure -input=false
terraform -chdir=infra/environments/dev validate

# 3. Plan (read-only, no apply)
#    Uses the same local backend override. Pass required secret vars as stubs.
terraform -chdir=infra/environments/dev plan -input=false \
  -var="jwt_secret_key=dummy" -var="smtp_password=dummy"
#    Expected: Plan summary line with zero errors.
#    Remove backend_override.tf immediately after — it must NEVER be committed.
```

**Pass criteria (all must be true):**
- `fmt -check` exits 0 on all changed directories
- `validate` output ends with `Success! The configuration is valid`
- `plan` output contains `Plan: N to add` with no `Error:` lines

## File Structure

```
infra/
├── environments/
│   ├── dev/          ← root module (main.tf, variables.tf, outputs.tf, provider.tf, terraform.tfvars)
│   └── prod/         ← root module
└── modules/
    └── <service>/    ← child module (main.tf, variables.tf, outputs.tf)
```

## Testing

Every module change requires a corresponding `.tftest.hcl` update in `infra/modules/<module>/tests/`.
