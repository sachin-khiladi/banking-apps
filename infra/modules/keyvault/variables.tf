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

variable "unique_suffix" {
  description = "Short suffix to guarantee globally unique Key Vault names (e.g. last 6 chars of subscription ID)"
  type        = string
}

variable "tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
}

variable "deployer_object_id" {
  description = "Object ID of the principal running Terraform (needs KV Administrator)"
  type        = string
}

variable "kv_sku" {
  description = "Key Vault SKU: standard | premium"
  type        = string
  default     = "standard"
}

variable "kv_soft_delete_retention_days" {
  description = "Days Key Vault soft-deleted objects are retained (7–90)"
  type        = number
  default     = 7
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
}

variable "smtp_password" {
  description = "SMTP password to store as a Key Vault secret"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
