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

variable "log_retention_days" {
  type        = number
  description = "Log Analytics data retention in days (30–730)"
  default     = 30

  validation {
    condition     = var.log_retention_days >= 30 && var.log_retention_days <= 730
    error_message = "log_retention_days must be between 30 and 730. Got: ${var.log_retention_days}."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
