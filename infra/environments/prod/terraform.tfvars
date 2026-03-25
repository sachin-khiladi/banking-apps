# ===========================================================================
# prod environment — terraform.tfvars
# Deploy:  cd environments/prod && terraform init && terraform apply
# ===========================================================================

env      = "prod"
location = "eastus"

# ---------------------------------------------------------------------------
# Container image
# Replace with your ACR image before applying to production:
#   acrbankapiprod.azurecr.io/bank-api:stable
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
smtp_host       = "smtp.office365.com"
smtp_port       = 587
smtp_username   = "noreply@example.com"
smtp_from_email = "noreply@example.com"
smtp_password   = "replace-me"
