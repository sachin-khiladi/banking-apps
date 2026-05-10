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

variable "deployer_object_id" {
  description = "Object ID of the deploying principal to grant AcrPush (CI/CD or developer)"
  type        = string

  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.deployer_object_id))
    error_message = "deployer_object_id must be a valid GUID."
  }
}

variable "deployer_acr_push_role_assignment_name" {
  description = "Optional existing role assignment GUID for deployer AcrPush at this ACR scope. Set this when AcrPush already exists so Terraform adopts the existing assignment instead of creating a duplicate."
  type        = string
  default     = null

  validation {
    condition     = var.deployer_acr_push_role_assignment_name == null || can(regex("^([0-9a-fA-F]{32}|[0-9a-fA-F-]{36})$", trimspace(var.deployer_acr_push_role_assignment_name)))
    error_message = "deployer_acr_push_role_assignment_name must be null, a 32-character GUID, or a 36-character hyphenated GUID."
  }
}

variable "project_repository_path" {
  description = "Repository path prefix enforced for deployer push/pull access (for example: project/fastapi-azure-app)."
  type        = string

  validation {
    condition     = can(regex("^project/[a-z0-9][a-z0-9._-]*$", var.project_repository_path))
    error_message = "project_repository_path must match 'project/<project-name>' using lowercase letters, digits, dots, underscores, or hyphens."
  }
}

variable "enforce_project_repository_abac" {
  description = "When true, applies an ABAC condition to the deployer AcrPush assignment so access is limited to project_repository_path."
  type        = bool
  default     = true
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

variable "deployer_repository_condition" {
  description = "Optional ABAC condition expression override (condition_version 2.0) for the deployer AcrPush role assignment. Leave null to use the module default project path condition."
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
