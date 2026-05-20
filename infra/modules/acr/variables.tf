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
  description = "Short application name (alphanumeric, included in ACR name)"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9]*$", var.app_name))
    error_message = "app_name must start with a lowercase letter and contain only lowercase letters and digits for ACR naming."
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

variable "unique_suffix" {
  description = "Short unique suffix to keep ACR name globally unique (e.g. last 6 chars of subscription ID)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{6}$", var.unique_suffix))
    error_message = "unique_suffix must be exactly 6 lowercase alphanumeric characters."
  }
}

variable "acr_sku" {
  description = "ACR SKU: Basic | Standard | Premium"
  type        = string
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "acr_sku must be one of: Basic, Standard, Premium."
  }
}

variable "uami_principal_id" {
  description = "Principal ID of the UAMI to grant AcrPull"
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.uami_principal_id))
    error_message = "uami_principal_id must be a valid GUID."
  }
}

variable "enforce_acr_role_assignment_mode" {
  description = "When true, configures the ACR registry roleAssignmentMode property via ARM to ensure ABAC repository permissions are active."
  type        = bool
  default     = true
}

variable "acr_role_assignment_mode" {
  description = "Role assignment mode for ACR repository permissions. Use AbacRepositoryPermissions for RBAC+ABAC and LegacyRegistryPermissions for legacy behavior."
  type        = string
  default     = "AbacRepositoryPermissions"

  validation {
    condition     = contains(["AbacRepositoryPermissions", "LegacyRegistryPermissions"], var.acr_role_assignment_mode)
    error_message = "acr_role_assignment_mode must be AbacRepositoryPermissions or LegacyRegistryPermissions."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
