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
