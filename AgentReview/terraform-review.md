# Terraform Code Review (GPT-5.3-Codex)

Scope: read-only review of Terraform root/modules and environment tfvars under `infra/`.

## TF-001
- Severity: Medium
- Category: Governance
- Location: `infra/environments/prod/terraform.tfvars:32`, `infra/environments/dev/terraform.tfvars:32`
- Rule: Infrastructure bootstrap artifacts should use immutable container references (versioned tag or digest), not mutable rolling tags.
- Evidence: Both environments set `container_image = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"`.
- Impact: Upstream `latest` can change without repo change, reducing reproducibility and weakening forensic traceability for infra bootstrap events.
- Recommendation: Pin bootstrap image to immutable digest (`@sha256:...`) and keep CD-owned runtime image updates separate as already designed.
- Grounding: Deterministic artifact identity is a baseline supply-chain control for auditable infrastructure provisioning.

## TF-002
- Severity: Medium
- Category: Correctness
- Location: `infra/environments/prod/variables.tf:71-73`
- Rule: Production image validation should prevent mutable tags on deployable ACR images.
- Evidence: Prod validation accepts `*.azurecr.io/...:.+` and therefore permits mutable tags (for example `:latest`) for ACR references.
- Impact: Mutable tags in production can cause non-repeatable releases and ambiguous rollback state.
- Recommendation: Tighten prod validation to reject mutable tags for ACR images (allowing only immutable/versioned tags or digest form), while retaining explicit bootstrap exception.
- Grounding: Release governance standards require immutable production artifact references to guarantee deployment determinism.

## TF-003
- Severity: Medium
- Category: Governance
- Location: `infra/environments/dev/variables.tf:65-67`, `infra/environments/prod/variables.tf:65-75`
- Rule: Environment policy parity should be explicit where drift can bypass controls.
- Evidence: Dev validation only checks `container_image` non-empty, while prod uses stricter ACR-or-bootstrap rule.
- Impact: Inconsistent policy allows invalid/non-standard image references to pass in dev, reducing confidence that dev plan/apply behavior is representative of prod.
- Recommendation: Align dev validation to the same structural rule as prod (possibly with controlled exceptions), or document intentional divergence with explicit risk acceptance.
- Grounding: Policy parity between lower and higher environments improves pre-production signal quality and reduces promotion surprises.

## TF-004
- Severity: Low
- Category: Reliability
- Location: `infra/environments/dev/provider.tf:27`, `infra/environments/prod/provider.tf:25`
- Rule: Provider registration strategy must include deterministic bootstrap checks when auto-registration is disabled.
- Evidence: `resource_provider_registrations = "none"` is configured in both environments.
- Impact: Applies can fail in newly provisioned subscriptions/tenants when required providers are not already registered.
- Recommendation: Keep the setting if intentional, but enforce preflight provider-registration checks in infra bootstrap workflows before plan/apply.
- Grounding: Explicit prerequisite enforcement reduces intermittent environment bootstrap failures.

## Positive Controls Observed
- `lifecycle.ignore_changes` on container image in `infra/modules/container_app/main.tf` cleanly enforces Terraform-vs-CD ownership separation.
- Sensitive inputs are marked (`sensitive = true`) for secret-bearing variables in environment roots.
- Remote state uses AzureRM backend with Azure AD + OIDC in both environments.
