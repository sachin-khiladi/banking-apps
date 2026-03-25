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
  description = "Memory per replica (e.g. 2Gi)"
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
  default     = true
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
  default     = 7
}

variable "acr_sku" {
  type        = string
  description = "Azure Container Registry SKU: Basic | Standard | Premium"
  default     = "Standard"

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

variable "cosmos_db_name" {
  type        = string
  description = "Cosmos DB SQL database name"
  default     = "banking"
}

variable "enable_serverless" {
  type        = bool
  description = "Enable Cosmos DB serverless capacity mode (false = provisioned autoscale for prod)"
  default     = false
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

variable "smtp_from_email" {
  type        = string
  description = "From email used for statement delivery"

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.smtp_from_email))
    error_message = "smtp_from_email must be a valid email address. Got: \"${var.smtp_from_email}\"."
  }
}

variable "smtp_password" {
  type        = string
  description = "SMTP password stored in Key Vault"
  sensitive   = true
}
