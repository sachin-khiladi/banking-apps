variable "resource_group_id" {
  type        = string
  description = "Resource ID of the resource group where bootstrap RBAC assignments are created."
}

variable "enabled" {
  type        = bool
  description = "Whether bootstrap RBAC role assignments are created."
  default     = true
}

variable "deployment_principal_object_id" {
  type        = string
  description = "Object ID of the deployment principal that receives bootstrap RBAC assignments."

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.deployment_principal_object_id))
    error_message = "deployment_principal_object_id must be a valid GUID."
  }
}

variable "role_definition_names" {
  type        = list(string)
  description = "Built-in role names assigned to the deployment principal at resource-group scope."
  default     = ["User Access Administrator", "Contributor"]

  validation {
    condition     = contains(var.role_definition_names, "User Access Administrator")
    error_message = "role_definition_names must include 'User Access Administrator'."
  }

  validation {
    condition     = contains(var.role_definition_names, "Contributor")
    error_message = "role_definition_names must include 'Contributor' for provisioning coverage."
  }
}

variable "skip_service_principal_aad_check" {
  type        = bool
  description = "Skips AAD lookup checks for service principal propagation when assigning RBAC roles."
  default     = true
}