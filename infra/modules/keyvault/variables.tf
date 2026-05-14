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

  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be one of: dev, staging, prod."
  }
}

variable "unique_suffix" {
  description = "Short suffix to guarantee globally unique Key Vault names (e.g. last 6 chars of subscription ID)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{6}$", var.unique_suffix))
    error_message = "unique_suffix must be exactly 6 lowercase alphanumeric characters."
  }
}

variable "tenant_id" {
  description = "Azure AD tenant ID"
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.tenant_id))
    error_message = "tenant_id must be a valid GUID."
  }
}

variable "deployer_object_id" {
  description = "Object ID of the principal running Terraform (needs KV Administrator)"
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.deployer_object_id))
    error_message = "deployer_object_id must be a valid GUID."
  }
}

variable "kv_sku" {
  description = "Key Vault SKU: standard | premium"
  type        = string
  default     = "standard"

  validation {
    condition     = contains(["standard", "premium"], var.kv_sku)
    error_message = "kv_sku must be one of: standard, premium."
  }
}

variable "kv_soft_delete_retention_days" {
  description = "Days Key Vault soft-deleted objects are retained (7–90)"
  type        = number
  default     = 7

  validation {
    condition     = var.kv_soft_delete_retention_days >= 7 && var.kv_soft_delete_retention_days <= 90
    error_message = "kv_soft_delete_retention_days must be between 7 and 90."
  }
}

variable "purge_protection_enabled" {
  description = "Enable purge protection (required for prod)"
  type        = bool
  default     = false
}

variable "app_insights_connection_string" {
  description = "Application Insights connection string to store as a KV secret"
  type        = string
  sensitive   = true

  validation {
    condition     = trimspace(var.app_insights_connection_string) != ""
    error_message = "app_insights_connection_string must not be empty."
  }
}

variable "jwt_secret_key" {
  description = "JWT signing secret to store as a Key Vault secret"
  type        = string
  sensitive   = true

  validation {
    condition     = trimspace(var.jwt_secret_key) != ""
    error_message = "jwt_secret_key must not be empty."
  }
}

variable "smtp_password" {
  description = "SMTP password to store as a Key Vault secret"
  type        = string
  sensitive   = true

  validation {
    condition     = trimspace(var.smtp_password) != ""
    error_message = "smtp_password must not be empty."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "rbac_propagation_wait_seconds" {
  description = "Seconds to wait after deployer Key Vault Administrator role assignment before secret operations."
  type        = number
  default     = 90

  validation {
    condition     = var.rbac_propagation_wait_seconds >= 0 && var.rbac_propagation_wait_seconds <= 600
    error_message = "rbac_propagation_wait_seconds must be between 0 and 600."
  }
}
