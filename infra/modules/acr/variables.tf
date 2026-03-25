variable "resource_group_name" {
  description = "Name of the resource group to deploy into"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "app_name" {
  description = "Short application name (alphanumeric, included in ACR name)"
  type        = string
}

variable "env" {
  description = "Deployment environment (dev | prod)"
  type        = string
}

variable "unique_suffix" {
  description = "Short unique suffix to keep ACR name globally unique (e.g. last 6 chars of subscription ID)"
  type        = string
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
}

variable "deployer_object_id" {
  description = "Object ID of the deploying principal to grant AcrPush (CI/CD or developer)"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
