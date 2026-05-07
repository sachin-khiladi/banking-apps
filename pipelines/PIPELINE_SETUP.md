# CI/CD Pipelines — Azure DevOps Setup Guide

Two pipelines manage infrastructure deployment:

| Pipeline | File | Trigger |
|----------|------|---------|
| **TF · Infra Plan** | `pipelines/tf-infra-plan.yml` | Every PR to `main` touching `infra/` |
| **TF · Infra Apply** | `pipelines/tf-infra-apply.yml` | Manual only (run from ADO UI or CLI) |

GitHub Actions also manages infra/app deployment:

| Workflow | File | Trigger |
|----------|------|---------|
| **PR Python Checks** | `.github/workflows/pr.yml` | PRs touching Python code and tests |
| **Terraform Infra Plan** | `.github/workflows/infra-terraform.yml` | PRs touching `infra/**` |
| **Main Dev Release** | `.github/workflows/main-dev-release.yml` | Push to `main` (single orchestrated release flow) |
| **CI (legacy fallback)** | `.github/workflows/ci.yml` | Manual dispatch only |

GitHub deployment order is now strict infra-first:

1. Push merge commit to `main`
2. `Main Dev Release` runs Terraform plan
3. Manual approval is required on `banking-dev` before Terraform apply
4. After infra apply succeeds, Python build job runs and publishes image metadata
5. Deploy job consumes that metadata and deploys the exact image digest

---

## Review-before-deploy flow

```
PR opened (infra/** changed)
  └─ tf-infra-plan runs automatically
       ├── Plan · dev  → posts plan as PR comment in ADO Repos
       └── Plan · prod → posts plan as PR comment in ADO Repos
              ↓
           Review plan comments → merge PR
              ↓
           (nothing deploys automatically)
              ↓
Run tf-infra-apply manually
  ├── PlanPreview stage  →  full plan written to pipeline Summary tab
  ├── ─── [ADO Environment approval gate for bankapi-prod] ───────────
  │          Approver: Pipelines → run → Summary tab (reads plan)
  │                              → Review → Approve
  └── Apply stage
       ├── re-plans fresh (guards state drift)
       └── terraform apply
```

---

## Step 1 — Create Service Connections (Workload Identity Federation)

In ADO: **Project Settings → Service connections → New service connection**

Connection type: **Azure Resource Manager**
Authentication method: **Workload Identity Federation (automatic)**

Create two connections:

| Connection name | Purpose |
|----------------|---------|
| `sc-bankapi-dev-tf` | Terraform operations on the dev environment |
| `sc-bankapi-prod-tf` | Terraform operations on the prod environment |

For each connection:
1. Select **Subscription** scope
2. Pick subscription: `b86177f7-23c4-4a3a-b37f-5c4c8775af34`
3. Name it exactly as shown above
4. Tick **Grant access permission to all pipelines**  *(or grant per-pipeline after creation)*

ADO creates the managed identity automatically when you choose "automatic" WIF.

---

## Step 2 — Assign Azure RBAC to the Service Connection Identities

After creating each service connection, find its managed identity:
**Project Settings → Service connections → select connection → Manage Service Principal → copy Object ID**

Then assign roles:

```bash
SUBSCRIPTION_ID="b86177f7-23c4-4a3a-b37f-5c4c8775af34"
BACKEND_RG="rg-tf-backend"
BACKEND_SA="strgtfbackendb86177"

# Replace with the Object IDs of each service connection's managed identity
DEV_SP_OID="<object-id-of-sc-bankapi-dev-tf>"
PROD_SP_OID="<object-id-of-sc-bankapi-prod-tf>"

# ── Dev service connection ────────────────────────────────────────────────────
az role assignment create \
  --assignee-object-id "$DEV_SP_OID" \
  --role "Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID" \
  --assignee-principal-type ServicePrincipal

az role assignment create \
  --assignee-object-id "$DEV_SP_OID" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$BACKEND_RG/providers/Microsoft.Storage/storageAccounts/$BACKEND_SA" \
  --assignee-principal-type ServicePrincipal

# ── Prod service connection ───────────────────────────────────────────────────
az role assignment create \
  --assignee-object-id "$PROD_SP_OID" \
  --role "Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID" \
  --assignee-principal-type ServicePrincipal

az role assignment create \
  --assignee-object-id "$PROD_SP_OID" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$BACKEND_RG/providers/Microsoft.Storage/storageAccounts/$BACKEND_SA" \
  --assignee-principal-type ServicePrincipal
```

> **Tip — least privilege in production:**  
> Once `rg-bankapi-prod` has been created on the first manual apply, scope the prod
> service connection down to that resource group instead of the whole subscription.

---

## Step 3 — Create ADO Environments

ADO Environments are what the Apply pipeline uses as its approval gate.

In ADO: **Pipelines → Environments → New environment**

Create two environments:

| Environment name | Approval required |
|-----------------|-------------------|
| `bankapi-dev` | No |
| `bankapi-prod` | **Yes** — configure below |

### Configure approval check on `bankapi-prod`

1. Go to **Pipelines → Environments → bankapi-prod**
2. Click **...** → **Approvals and checks → +**
3. Choose **Approvals**
4. Add approvers (e.g. your team leads / platform team)
5. Set **Timeout** (e.g. 8 hours)
6. Save

When the Apply pipeline runs for prod, it pauses at the Apply stage and sends an email
to approvers. The approver:
1. Opens the pipeline run link
2. Clicks the **Summary** tab — the full Terraform plan is displayed there
3. Reviews the plan, then clicks **Review → Approve** (or Reject)

---

## Step 4 — Create Pipeline Definitions in ADO

In ADO: **Pipelines → New pipeline → Azure Repos Git → select repo → Existing YAML file**

| Pipeline name | YAML file path |
|--------------|----------------|
| `TF · Infra Plan` | `/pipelines/tf-infra-plan.yml` |
| `TF · Infra Apply` | `/pipelines/tf-infra-apply.yml` |

After creating each pipeline:

**Enable OAuth token for PR comments** (required for the plan pipeline to post comments):
1. Edit the `TF · Infra Plan` pipeline
2. Click **...** → **Triggers**
3. Under **YAML** tab → click the pipeline → **Agent job**
4. Enable **Allow scripts to access the OAuth token**

*Alternatively*, this can be set programmatically:
```bash
az pipelines update --name "TF · Infra Plan" \
  --project "<your-ado-project>" \
  --organization "https://dev.azure.com/<your-org>"
# Then in the pipeline YAML you can also set it per-step via the
# env: SYSTEM_ACCESSTOKEN: $(System.AccessToken) mapping (already done in the YAML)
```

---

## Step 5 — Set Branch Policy (plan pipeline as PR gate)

In ADO: **Project Settings → Repositories → select repo → Policies → Branch policies → main**

Add a **Build validation** policy:
- Build pipeline: `TF · Infra Plan`
- Trigger: Automatic
- Policy requirement: Required
- Display name: `Terraform Plan — dev + prod`

This blocks PR merges until both plan-dev and plan-prod stages succeed.

---

## Workflow reference

| Situation | Action |
|-----------|--------|
| Routine infra change | Open PR → review plan PR comments → merge |
| Deploy to dev | Run **TF · Infra Apply** → `environment=dev` → fill reason → auto-proceeds |
| Deploy to prod | Run **TF · Infra Apply** → `environment=prod` → fill reason → approver reads plan in Summary tab → approves |
| Check what would change without a PR | Run **TF · Infra Plan** manually → pick environment |

GitHub Actions reference:

| Situation | Action |
|-----------|--------|
| Validate Python changes on PR | `PR Python Checks` runs automatically |
| Validate Terraform changes on PR | `Terraform Infra Plan` runs automatically |
| Deploy app in dev after merge | `Main Dev Release` runs plan -> approval -> apply -> build -> deploy |
| Run legacy fallback build manually | `CI` can be run with manual dispatch |

---

## GitHub Actions — Azure authentication and required repository variables

The GitHub workflows use federated identity (`azure/login`) with generalized repository variables.

### Required repository variables for `main-dev-release.yml`, reusable ACA deploy, and `.github/workflows/infra-terraform.yml`

The following three variables must be set manually (once) before any workflow runs:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

Recommended: define these as repository-level variables, or environment-level variables if you later need per-environment identities.

### Required repository secrets for image publish

The main release workflow pushes container images to ACR and requires:

- `ACR_USERNAME`
- `ACR_PASSWORD`

### Optional legacy auto-populated variables (manual fallback path)

The following variables are still written by `infra-apply-dev.yml` for the legacy manual workflow path. The new `main-dev-release.yml` flow uses Terraform outputs directly inside the same run and does not depend on these variables.

| Variable | Set by | Value source |
|----------|--------|--------------|
| `AZURE_RESOURCE_GROUP_DEV` | `infra-apply-dev.yml` | `terraform output resource_group_name` |
| `CONTAINER_APP_NAME_DEV` | `infra-apply-dev.yml` | `terraform output container_app_name` |
| `ACR_LOGIN_SERVER_DEV` | `infra-apply-dev.yml` | `terraform output acr_login_server` |

These variables are consumed by legacy workflows only.

---

## Variable and secret inventory

Azure DevOps Terraform pipelines (`pipelines/tf-infra-plan.yml`, `pipelines/tf-infra-apply.yml`) do not require ADO secret variables when using Workload Identity Federation service connections.

GitHub Actions workflows require Azure auth values from GitHub Variables (listed above), and pass them into `azure/login` and Terraform via `ARM_CLIENT_ID`, `ARM_TENANT_ID`, `ARM_SUBSCRIPTION_ID`.

If you ever need to override the Terraform version, edit the `TF_VERSION` variable
at the top of either YAML file (or override it as a pipeline-level variable in ADO).
