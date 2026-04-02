# Pre-Destroy / Recreate Checklist (Dev)

## Scope
- Resource group: `rg-bankapi-dev`
- Parity mode: Terraform-managed resources only
- Inventory command wrapper: `scripts/run_terraform_parity_audit.sh`

## Pre-Destroy Safety
- [ ] Confirm Azure account context targets the correct subscription and tenant.
- [ ] Run parity baseline: `bash scripts/run_terraform_parity_audit.sh`.
- [ ] Verify report has `missing_in_tf: 0` and `missing_in_azure: 0` in `agents-communication/reports/terraform-parity-report.md`.
- [ ] Confirm no uncommitted Terraform module changes that should be included before recreate.
- [ ] Confirm backend state storage is reachable (`infra/environments/dev` backend).
- [ ] Check Key Vault soft-delete expectations for recreate (`kv-bankapi-dev-*`).
- [ ] Confirm required image exists in ACR if app deploy expects existing tag.

## Destroy Sequence
- [ ] `terraform -chdir=infra/environments/dev init -input=false`
- [ ] `terraform -chdir=infra/environments/dev plan -destroy -out=tfplan-destroy`
- [ ] Review destroy plan carefully.
- [ ] `terraform -chdir=infra/environments/dev apply tfplan-destroy`

## Recreate Sequence
- [ ] `terraform -chdir=infra/environments/dev init -input=false`
- [ ] `terraform -chdir=infra/environments/dev plan -out=tfplan-apply`
- [ ] Review apply plan.
- [ ] `terraform -chdir=infra/environments/dev apply tfplan-apply`

## Post-Recreate Validation
- [ ] Run parity again: `bash scripts/run_terraform_parity_audit.sh`.
- [ ] Confirm parity report still shows zero missing resources.
- [ ] Validate Container App ingress and latest revision are healthy.
- [ ] Validate Key Vault secret references resolve in Container App.
- [ ] Validate Cosmos DB RBAC assignment for app UAMI is present.

## Quality Gates
- [ ] `terraform fmt -check -recursive infra/`
- [ ] `terraform -chdir=infra/environments/dev validate`

## Outputs to Archive
- `agents-communication/reports/terraform-parity-report.md`
- `agents-communication/reports/terraform-parity-report.json`
- `agents-communication/reports/live-rg-bankapi-dev.normalized.json`
- `agents-communication/reports/tf-dev-managed-resources.normalized.json`
