variable "resource_group_name" {
  type        = string
  description = "Name of the resource group to deploy into."
}

variable "location" {
  type        = string
  description = "Azure region for all resources in this module."
}

variable "app_name" {
  type        = string
  description = "Short application name used as a naming prefix."

  validation {
    condition     = can(regex("^[a-z0-9]+$", var.app_name))
    error_message = "app_name must contain only lowercase letters and digits."
  }
}

variable "env" {
  type        = string
  description = "Deployment environment (dev | staging | prod)."

  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be one of: dev, staging, prod."
  }
}

variable "unique_suffix" {
  type        = string
  description = "6-character suffix for globally unique resource names."

  validation {
    condition     = length(var.unique_suffix) == 6 && can(regex("^[a-z0-9]+$", var.unique_suffix))
    error_message = "unique_suffix must be exactly 6 lowercase alphanumeric characters."
  }
}

variable "account_tier" {
  type        = string
  description = "Storage account tier: Standard | Premium."
  default     = "Standard"

  validation {
    condition     = contains(["Standard", "Premium"], var.account_tier)
    error_message = "account_tier must be one of: Standard, Premium."
  }
}

variable "account_replication_type" {
  type        = string
  description = "Storage account replication: LRS | GRS | RAGRS | ZRS | GZRS | RAGZRS."
  default     = "LRS"

  validation {
    condition     = contains(["LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"], var.account_replication_type)
    error_message = "account_replication_type must be one of: LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS."
  }
}

variable "access_tier" {
  type        = string
  description = "Access tier for Blob Storage: Hot | Cool."
  default     = "Hot"

  validation {
    condition     = contains(["Hot", "Cool"], var.access_tier)
    error_message = "access_tier must be one of: Hot, Cool."
  }
}

variable "enable_hns" {
  type        = bool
  description = "Enable hierarchical namespace (Data Lake Storage Gen2)."
  default     = false
}

variable "allow_blob_public_access" {
  type        = bool
  description = "Allow public access to blobs."
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to all resources in this module."
  default     = {}
}
