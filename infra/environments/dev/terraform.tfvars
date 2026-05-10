# ===========================================================================
# dev environment — terraform.tfvars
# Deploy:  cd environments/dev && terraform init && terraform apply
# ===========================================================================

env          = "dev"
location     = "eastus"
cost_center  = "banking-platform"
project_name = "fastapi-azure-app"

# Optional override for deployment principal object ID used by bootstrap/deployer RBAC.
# Set to null to use the currently authenticated principal.
deployment_principal_object_id = null

# RBAC bootstrap — disabled because the CI/CD service principal cannot
# self-assign roleAssignments/write (circular bootstrap deadlock).
# Prerequisite: grant the CI SP 'User Access Administrator' (with ABAC condition)
# or 'Owner' at subscription scope via the Azure portal or az CLI before enabling.
# See: infra/modules/rbac_bootstrap/README.md
rbac_bootstrap_enabled               = false
rbac_bootstrap_role_definition_names = ["User Access Administrator", "Contributor"]
rbac_bootstrap_skip_sp_aad_check     = true

# ---------------------------------------------------------------------------
# Container image — immutable bootstrap placeholder for initial infrastructure provisioning only.
# Terraform provisions the Container App with this public image so that infra
# apply succeeds without requiring an ACR image to exist first.
# The CD workflow (.github/workflows/cd.yml) owns the real app image
# and will update the Container App revision after every app code push.
# Terraform ignores image changes after initial provisioning
# (lifecycle.ignore_changes in modules/container_app/main.tf).
# ---------------------------------------------------------------------------
container_image = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"

# Container sizing — lightweight for dev
container_cpu    = 0.5
container_memory = "1Gi"
container_port   = 8000

# Scaling — single replica in dev is sufficient
min_replicas = 0 # scale to zero when idle to save cost
max_replicas = 1

# Monitoring — short retention for dev
log_retention_days = 30

# Key Vault — minimum soft-delete (7 days is the minimum allowed by Azure)
kv_soft_delete_retention_days = 7

# Azure Container Registry
# Basic SKU is sufficient for dev (no geo-replication, lower cost)
acr_sku = "Basic"

# Cosmos DB
# Serverless mode: no pre-provisioned RU/s, pay per request — ideal for dev
# cosmos_location overrides the region for CosmosDB only (eastus has zone-redundant
# capacity constraints; eastus2 is used as a fallback without moving other resources).
cosmos_db_name    = "banking"
enable_serverless = true
cosmos_location   = "eastus2"

# SMTP settings for bank statement email delivery
smtp_host         = "smtp.office365.com"
smtp_port         = 587
smtp_username     = "noreply@example.com"
smtp_sender_email = "noreply@example.com"
smtp_password     = "replace-me"
jwt_secret_key    = "replace-me"

# Optional SMTP toggles
smtp_use_tls         = true
smtp_timeout_seconds = 15

# ---------------------------------------------------------------------------
# If this is your first deploy, push the image to ACR before `terraform apply`.
# Expected login server for dev:
#   acrbankapidevc8775a.azurecr.io/bank-api:latest
# Run: az acr login --name <acr_name>
#      docker build -t <acr_login_server>/bank-api:latest .
#      docker push <acr_login_server>/bank-api:latest
# ---------------------------------------------------------------------------
