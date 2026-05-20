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

variable "app_identity_principal_id" {
  description = "Principal ID of the UAMI that the Container App uses (gets Data Reader role)"
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.app_identity_principal_id))
    error_message = "app_identity_principal_id must be a valid GUID."
  }
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

variable "soft_delete_retention_days" {
  description = "Soft-delete retention days (1–7 for standard, 0 for free)"
  type        = number
  default     = 1

  validation {
    condition     = (var.app_config_sku == "free" && var.soft_delete_retention_days == 0) || (var.app_config_sku == "standard" && var.soft_delete_retention_days >= 1 && var.soft_delete_retention_days <= 7)
    error_message = "soft_delete_retention_days must be 0 for free SKU, or between 1 and 7 for standard SKU."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

