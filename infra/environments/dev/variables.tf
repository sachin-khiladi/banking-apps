variable "env" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be one of: dev, staging, prod. Got: \"${var.env}\"."
  }
}

variable "location" {
  type        = string
  description = "Azure region for all resources"
}

variable "deployment_principal_object_id" {
  type        = string
  description = "Object ID of the deployment principal used for bootstrap and deployer RBAC assignments. Defaults to the current principal when null."
  default     = null
  nullable    = true
}

variable "rbac_bootstrap_enabled" {
  type        = bool
  description = "Enable bootstrap RBAC role assignments for the deployment principal at resource-group scope."
  default     = true
}

variable "rbac_bootstrap_role_definition_names" {
  type        = list(string)
  description = "Built-in role names assigned to the deployment principal during bootstrap."
  default     = ["User Access Administrator", "Contributor"]

  validation {
    condition     = contains(var.rbac_bootstrap_role_definition_names, "User Access Administrator")
    error_message = "rbac_bootstrap_role_definition_names must include 'User Access Administrator'."
  }

  validation {
    condition     = contains(var.rbac_bootstrap_role_definition_names, "Contributor")
    error_message = "rbac_bootstrap_role_definition_names must include 'Contributor'."
  }
}

variable "rbac_bootstrap_skip_sp_aad_check" {
  type        = bool
  description = "Skip AAD service-principal propagation checks while creating bootstrap role assignments."
  default     = true
}

variable "container_image" {
  type        = string
  description = "Container image to deploy (registry/image:tag)"
}

variable "container_cpu" {
  type        = number
  description = "vCPU per replica"
}

variable "container_memory" {
  type        = string
  description = "Memory per replica (e.g. 1Gi)"
}

variable "min_replicas" {
  type        = number
  description = "Minimum replicas"
}

variable "max_replicas" {
  type        = number
  description = "Maximum replicas"
}

variable "container_port" {
  type        = number
  description = "Port the container listens on"
}

variable "log_retention_days" {
  type        = number
  description = "Log Analytics retention in days"

  validation {
    condition     = var.log_retention_days >= 30 && var.log_retention_days <= 730
    error_message = "log_retention_days must be between 30 and 730. Got: ${var.log_retention_days}."
  }
}

variable "kv_soft_delete_retention_days" {
  type        = number
  description = "Key Vault soft-delete retention days"

  validation {
    condition     = var.kv_soft_delete_retention_days >= 7 && var.kv_soft_delete_retention_days <= 90
    error_message = "kv_soft_delete_retention_days must be between 7 and 90. Got: ${var.kv_soft_delete_retention_days}."
  }
}

variable "kv_sku" {
  type        = string
  description = "Key Vault SKU: standard | premium"
  default     = "standard"

  validation {
    condition     = contains(["standard", "premium"], var.kv_sku)
    error_message = "kv_sku must be one of: standard, premium. Got: \"${var.kv_sku}\"."
  }
}

variable "purge_protection_enabled" {
  type        = bool
  description = "Enable Key Vault purge protection. Should be false in dev, true in prod."
  default     = false
}

variable "app_config_sku" {
  type        = string
  description = "App Configuration SKU: free | standard"
  default     = "standard"

  validation {
    condition     = contains(["free", "standard"], var.app_config_sku)
    error_message = "app_config_sku must be one of: free, standard. Got: \"${var.app_config_sku}\"."
  }
}

variable "app_config_soft_delete_days" {
  type        = number
  description = "App Configuration soft-delete retention days (1–7 for standard, 0 for free)"
  default     = 1
}

variable "acr_sku" {
  type        = string
  description = "Azure Container Registry SKU: Basic | Standard | Premium"
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "acr_sku must be one of: Basic, Standard, Premium. Got: \"${var.acr_sku}\"."
  }
}

variable "storage_account_tier" {
  type        = string
  description = "Storage account tier: Standard | Premium"
  default     = "Standard"

  validation {
    condition     = contains(["Standard", "Premium"], var.storage_account_tier)
    error_message = "storage_account_tier must be one of: Standard, Premium. Got: \"${var.storage_account_tier}\"."
  }
}

variable "storage_account_replication_type" {
  type        = string
  description = "Storage account replication: LRS | GRS | RAGRS | ZRS | GZRS | RAGZRS"
  default     = "LRS"

  validation {
    condition     = contains(["LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"], var.storage_account_replication_type)
    error_message = "storage_account_replication_type must be one of: LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS. Got: \"${var.storage_account_replication_type}\"."
  }
}

variable "storage_account_access_tier" {
  type        = string
  description = "Storage account access tier: Hot | Cool"
  default     = "Hot"

  validation {
    condition     = contains(["Hot", "Cool"], var.storage_account_access_tier)
    error_message = "storage_account_access_tier must be one of: Hot, Cool. Got: \"${var.storage_account_access_tier}\"."
  }
}

variable "storage_account_enable_hns" {
  type        = bool
  description = "Enable hierarchical namespace (Data Lake Storage Gen2)."
  default     = false
}

variable "storage_account_allow_blob_public_access" {
  type        = bool
  description = "Allow public access to blobs."
  default     = false
}

variable "cosmos_location" {
  type        = string
  description = "Azure region for Cosmos DB. Defaults to var.location when null. Override to work around regional capacity constraints."
  default     = null
  nullable    = true
}

variable "cosmos_db_name" {
  type        = string
  description = "Cosmos DB SQL database name"
  default     = "banking"
}

variable "enable_serverless" {
  type        = bool
  description = "Enable Cosmos DB serverless capacity mode (true = dev, false = provisioned prod)"
  default     = true
}

variable "smtp_host" {
  type        = string
  description = "SMTP server host name"
}

variable "smtp_port" {
  type        = number
  description = "SMTP server port"

  validation {
    condition     = var.smtp_port >= 1 && var.smtp_port <= 65535
    error_message = "smtp_port must be between 1 and 65535. Got: ${var.smtp_port}."
  }
}

variable "smtp_username" {
  type        = string
  description = "SMTP username"
}

variable "smtp_sender_email" {
  type        = string
  description = "Sender email used for statement delivery"

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.smtp_sender_email))
    error_message = "smtp_sender_email must be a valid email address. Got: \"${var.smtp_sender_email}\"."
  }
}

variable "smtp_use_tls" {
  type        = bool
  description = "Enable SMTP TLS (SMTP_USE_TLS env var)"
  default     = true
}

variable "smtp_timeout_seconds" {
  type        = number
  description = "SMTP timeout in seconds (SMTP_TIMEOUT_SECONDS env var)"
  default     = 15

  validation {
    condition     = var.smtp_timeout_seconds >= 1 && var.smtp_timeout_seconds <= 120
    error_message = "smtp_timeout_seconds must be between 1 and 120. Got: ${var.smtp_timeout_seconds}."
  }
}

variable "smtp_password" {
  type        = string
  description = "SMTP password stored in Key Vault"
  sensitive   = true
}
