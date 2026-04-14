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

variable "cost_center" {
  type        = string
  description = "Cost center tag applied to all provisioned resources."

  validation {
    condition     = trimspace(var.cost_center) != ""
    error_message = "cost_center must not be empty."
  }
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
  description = "Container image to deploy (registry/image:tag or registry/image@sha256:digest)"

  validation {
    # Allow either an ACR image with immutable identity semantics
    # (versioned/non-latest tag or digest), or the well-known immutable
    # MCR bootstrap placeholder used during initial infra provisioning.
    # Terraform ignores image changes after first apply (lifecycle.ignore_changes
    # in modules/container_app/main.tf), so the placeholder is never deployed
    # to real traffic — CD always owns the running revision.
    condition = (
      can(regex("^[a-z0-9]+\\.azurecr\\.io/.+:(?!latest$)[A-Za-z0-9][A-Za-z0-9._-]*$", trimspace(var.container_image))) ||
      can(regex("^[a-z0-9]+\\.azurecr\\.io/.+@sha256:[a-fA-F0-9]{64}$", trimspace(var.container_image))) ||
      trimspace(var.container_image) == "mcr.microsoft.com/azuredocs/containerapps-helloworld@sha256:e9b3e7c34664c7cffd7144864b0e4eec369bfde80068f9095dc63b37058bec"
    )
    error_message = "container_image must be an immutable ACR image (*.azurecr.io/repo:<non-latest-tag> or *.azurecr.io/repo@sha256:<digest>) or the approved bootstrap placeholder digest."
  }
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

  validation {
    condition     = (var.app_config_sku == "free" && var.app_config_soft_delete_days == 0) || (var.app_config_sku == "standard" && var.app_config_soft_delete_days >= 1 && var.app_config_soft_delete_days <= 7)
    error_message = "app_config_soft_delete_days must be 0 for free SKU, or between 1 and 7 for standard SKU."
  }
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

  validation {
    condition     = trimspace(var.smtp_password) != ""
    error_message = "smtp_password must not be empty."
  }
}

variable "jwt_secret_key" {
  type        = string
  description = "JWT signing secret stored in Key Vault and injected into the Container App."
  sensitive   = true

  validation {
    condition     = trimspace(var.jwt_secret_key) != ""
    error_message = "jwt_secret_key must not be empty."
  }
}
