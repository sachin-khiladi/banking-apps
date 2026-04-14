variable "resource_group_name" {
  description = "Name of the resource group to deploy into"
  type        = string

  validation {
    condition     = trimspace(var.resource_group_name) != ""
    error_message = "resource_group_name must not be empty."
  }
}

variable "location" {
  description = "Azure region"
  type        = string

  validation {
    condition     = trimspace(var.location) != ""
    error_message = "location must not be empty."
  }
}

variable "app_name" {
  description = "Short application name used in resource names"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.app_name))
    error_message = "app_name must start with a lowercase letter and contain only lowercase letters, digits, and hyphens."
  }
}

variable "env" {
  description = "Deployment environment (dev | prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be one of: dev, staging, prod."
  }
}

# -- Observability ----------------------------------------------------------

variable "log_analytics_workspace_id" {
  description = "Log Analytics Workspace resource ID (for CAE log sink)"
  type        = string

  validation {
    condition     = startswith(var.log_analytics_workspace_id, "/subscriptions/")
    error_message = "log_analytics_workspace_id must be a valid Azure resource ID."
  }
}

# -- Container image --------------------------------------------------------

variable "container_image" {
  description = "Container image to deploy (registry/image:tag or registry/image@sha256:digest)"
  type        = string

  validation {
    condition     = can(regex("^.+/.+(:[^:@\\s]+|@sha256:[a-fA-F0-9]{64})$", trimspace(var.container_image)))
    error_message = "container_image must be in the format registry/repository:tag or registry/repository@sha256:<64-hex-digest>."
  }
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

  validation {
    condition     = can(regex("^[0-9]+(\\.[0-9]+)?Gi$", var.container_memory))
    error_message = "container_memory must use the Gi suffix, for example 1Gi or 2Gi."
  }
}

variable "min_replicas" {
  description = "Minimum container app replicas"
  type        = number
  default     = 1

  validation {
    condition     = var.min_replicas >= 0
    error_message = "min_replicas must be greater than or equal to 0."
  }
}

variable "max_replicas" {
  description = "Maximum container app replicas"
  type        = number
  default     = 3

  validation {
    condition     = var.max_replicas >= 1
    error_message = "max_replicas must be at least 1."
  }
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000

  validation {
    condition     = var.container_port >= 1 && var.container_port <= 65535
    error_message = "container_port must be between 1 and 65535."
  }
}

# -- Identity ---------------------------------------------------------------

variable "uami_id" {
  description = "Resource ID of the User-Assigned Managed Identity to attach"
  type        = string

  validation {
    condition     = startswith(var.uami_id, "/subscriptions/")
    error_message = "uami_id must be a valid Azure resource ID."
  }
}

variable "uami_client_id" {
  description = "Client ID of the UAMI (passed as AZURE_CLIENT_ID env var)"
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.uami_client_id))
    error_message = "uami_client_id must be a valid GUID."
  }
}

# -- Secrets (Key Vault versionless URIs) -----------------------------------

variable "appinsights_secret_versionless_id" {
  description = "KV versionless secret URI for the App Insights connection string"
  type        = string

  validation {
    condition     = startswith(var.appinsights_secret_versionless_id, "https://") && strcontains(var.appinsights_secret_versionless_id, "/secrets/")
    error_message = "appinsights_secret_versionless_id must be a Key Vault secret URI."
  }
}

variable "jwt_secret_key_secret_versionless_id" {
  description = "KV versionless secret URI for the JWT signing secret"
  type        = string

  validation {
    condition     = startswith(var.jwt_secret_key_secret_versionless_id, "https://") && strcontains(var.jwt_secret_key_secret_versionless_id, "/secrets/")
    error_message = "jwt_secret_key_secret_versionless_id must be a Key Vault secret URI."
  }
}

variable "smtp_password_secret_versionless_id" {
  description = "KV versionless secret URI for the SMTP password"
  type        = string

  validation {
    condition     = startswith(var.smtp_password_secret_versionless_id, "https://") && strcontains(var.smtp_password_secret_versionless_id, "/secrets/")
    error_message = "smtp_password_secret_versionless_id must be a Key Vault secret URI."
  }
}

# -- Cosmos DB -------------------------------------------------------------

variable "cosmos_account_url" {
  description = "Cosmos DB account endpoint URL (COSMOS_ACCOUNT_URL env var). Not sensitive — auth uses RBAC/DefaultAzureCredential."
  type        = string

  validation {
    condition     = startswith(var.cosmos_account_url, "https://")
    error_message = "cosmos_account_url must start with https://."
  }
}

variable "cosmos_db_name" {
  description = "Cosmos DB SQL database name (COSMOS_DB_NAME env var)"
  type        = string

  validation {
    condition     = trimspace(var.cosmos_db_name) != ""
    error_message = "cosmos_db_name must not be empty."
  }
}

# -- Endpoints --------------------------------------------------------------

variable "app_config_endpoint" {
  description = "Azure App Configuration endpoint URL"
  type        = string

  validation {
    condition     = startswith(var.app_config_endpoint, "https://")
    error_message = "app_config_endpoint must start with https://."
  }
}

variable "key_vault_uri" {
  description = "Key Vault URI"
  type        = string

  validation {
    condition     = startswith(var.key_vault_uri, "https://")
    error_message = "key_vault_uri must start with https://."
  }
}

# -- ACR --------------------------------------------------------------------

variable "acr_login_server" {
  description = "ACR login server FQDN (e.g. acrbankapidev c8775a.azurecr.io). When set, a registry pull block is added using the UAMI. Set to null to pull from public registries (e.g. MCR)."
  type        = string
  default     = null

  validation {
    condition     = var.acr_login_server == null || can(regex("^[a-z0-9]+\\.azurecr\\.io$", var.acr_login_server))
    error_message = "acr_login_server must be null or an Azure Container Registry login server ending in .azurecr.io."
  }
}

variable "smtp_host" {
  description = "SMTP server host name"
  type        = string

  validation {
    condition     = trimspace(var.smtp_host) != ""
    error_message = "smtp_host must not be empty."
  }
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

  validation {
    condition     = trimspace(var.smtp_username) != ""
    error_message = "smtp_username must not be empty."
  }
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
