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

variable "deployer_object_id" {
  description = "Object ID of the principal running Terraform (gets Data Owner role)"
  type        = string
}

variable "app_identity_principal_id" {
  description = "Principal ID of the UAMI that the Container App uses (gets Data Reader role)"
  type        = string
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
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
