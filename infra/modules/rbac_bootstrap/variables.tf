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
  description = "Built-in role names assigned to the deployment principal at resource-group scope. Typically 'User Access Administrator' (for roleAssignments/write) and 'Contributor' (for resource provisioning). NOTE: the principal executing Terraform must already hold roleAssignments/write at subscription or management-group scope — this module cannot self-bootstrap that permission."
  default     = ["User Access Administrator", "Contributor"]
}

variable "uaa_condition" {
  type        = string
  description = "ABAC condition expression (condition_version 2.0) applied to the User Access Administrator role assignment to constrain which role definition IDs the grantee may assign. Set to null to create an unconditioned assignment — only acceptable when the grantee scope is already tightly controlled. See: https://learn.microsoft.com/azure/role-based-access-control/conditions-overview"
  default     = null
}

variable "skip_service_principal_aad_check" {
  type        = bool
  description = "Skips AAD lookup checks for service principal propagation when assigning RBAC roles."
  default     = true
}