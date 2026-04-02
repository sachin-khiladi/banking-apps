# ===========================================================================
# dev environment — terraform.tfvars
# Deploy:  cd environments/dev && terraform init && terraform apply
# ===========================================================================

env      = "dev"
location = "eastus"

# ---------------------------------------------------------------------------
# Container image
# Dev defaults to the app image in ACR (must already exist):
#   acrbankapidevc8775a.azurecr.io/bank-api:latest
# ---------------------------------------------------------------------------
container_image = "acrbankapidevc8775a.azurecr.io/bank-api:fix-bcrypt-20260318021423"

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
