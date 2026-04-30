# ===========================================================================
# prod environment — terraform.tfvars
# Deploy:  cd environments/prod && terraform init && terraform apply
# ===========================================================================

env         = "prod"
location    = "eastus"
cost_center = "banking-platform"

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
# and will update the Container App revision after every approved deployment.
# Terraform ignores image changes after initial provisioning
# (lifecycle.ignore_changes in modules/container_app/main.tf).
# ---------------------------------------------------------------------------
container_image = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"

# Container sizing — larger resources for production load
container_cpu    = 1.0
container_memory = "2Gi"
container_port   = 8000

# Scaling — always-on with room to scale out
min_replicas = 2
max_replicas = 10

# Monitoring — longer retention for audit and troubleshooting
log_retention_days = 90

# Key Vault — maximum soft-delete retention in production (90 days)
kv_soft_delete_retention_days = 90

# Azure Container Registry
# Standard SKU for prod — better throughput, geo-replication ready
acr_sku = "Standard"

# Cosmos DB
# Provisioned autoscale throughput for predictable production performance
cosmos_db_name    = "banking"
enable_serverless = false

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
