variable "resource_group_name" {
  description = "Name of the resource group to deploy into"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "app_name" {
  description = "Short application name used in resource names"
  type        = string
}

variable "env" {
  description = "Deployment environment (dev | prod)"
  type        = string
}

# -- Observability ----------------------------------------------------------

variable "log_analytics_workspace_id" {
  description = "Log Analytics Workspace resource ID (for CAE log sink)"
  type        = string
}

# -- Container image --------------------------------------------------------

variable "container_image" {
  description = "Container image to deploy (registry/image:tag)"
  type        = string
}

variable "container_cpu" {
  description = "vCPU allocated per replica (0.25 | 0.5 | 0.75 | 1.0 | 1.25 | 1.5 | 1.75 | 2.0)"
  type        = number
  default     = 0.5
}

variable "container_memory" {
  description = "Memory allocated per replica (e.g. 1Gi, 2Gi)"
  type        = string
  default     = "1Gi"
}

variable "min_replicas" {
  description = "Minimum container app replicas"
  type        = number
  default     = 1
}

variable "max_replicas" {
  description = "Maximum container app replicas"
  type        = number
  default     = 3
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}

# -- Identity ---------------------------------------------------------------

variable "uami_id" {
  description = "Resource ID of the User-Assigned Managed Identity to attach"
  type        = string
}

variable "uami_client_id" {
  description = "Client ID of the UAMI (passed as AZURE_CLIENT_ID env var)"
  type        = string
}

# -- Secrets (Key Vault versionless URIs) -----------------------------------

variable "appinsights_secret_versionless_id" {
  description = "KV versionless secret URI for the App Insights connection string"
  type        = string
}

variable "smtp_password_secret_versionless_id" {
  description = "KV versionless secret URI for the SMTP password"
  type        = string
}

# -- Cosmos DB -------------------------------------------------------------

variable "cosmos_account_url" {
  description = "Cosmos DB account endpoint URL (COSMOS_ACCOUNT_URL env var). Not sensitive — auth uses RBAC/DefaultAzureCredential."
  type        = string
}

variable "cosmos_db_name" {
  description = "Cosmos DB SQL database name (COSMOS_DB_NAME env var)"
  type        = string
}

# -- Endpoints --------------------------------------------------------------

variable "app_config_endpoint" {
  description = "Azure App Configuration endpoint URL"
  type        = string
}

variable "key_vault_uri" {
  description = "Key Vault URI"
  type        = string
}

# -- ACR --------------------------------------------------------------------

variable "acr_login_server" {
  description = "ACR login server FQDN (e.g. acrbankapidev c8775a.azurecr.io). When set, a registry pull block is added using the UAMI. Set to null to pull from public registries (e.g. MCR)."
  type        = string
  default     = null
}

variable "smtp_host" {
  description = "SMTP server host name"
  type        = string
}

variable "smtp_port" {
  description = "SMTP server port"
  type        = number

  validation {
    condition     = var.smtp_port >= 1 && var.smtp_port <= 65535
    error_message = "smtp_port must be between 1 and 65535."
  }
}

variable "smtp_username" {
  description = "SMTP username"
  type        = string
}

variable "smtp_sender_email" {
  description = "Sender email address used by SMTP"
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.smtp_sender_email))
    error_message = "smtp_sender_email must be a valid email address."
  }
}

variable "smtp_use_tls" {
  description = "Enable SMTP TLS (SMTP_USE_TLS env var)"
  type        = bool
  default     = true
}

variable "smtp_timeout_seconds" {
  description = "SMTP timeout in seconds (SMTP_TIMEOUT_SECONDS env var)"
  type        = number
  default     = 15

  validation {
    condition     = var.smtp_timeout_seconds >= 1 && var.smtp_timeout_seconds <= 120
    error_message = "smtp_timeout_seconds must be between 1 and 120."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
