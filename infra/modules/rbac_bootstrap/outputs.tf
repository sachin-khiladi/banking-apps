output "role_assignment_ids" {
  description = "Map of bootstrap role names to role assignment IDs."
  value       = { for role_name, assignment in azurerm_role_assignment.bootstrap : role_name => assignment.id }
}

output "assigned_role_definition_names" {
  description = "Sorted set of bootstrap role names assigned at resource-group scope."
  value       = sort(keys(azurerm_role_assignment.bootstrap))
}

output "deployment_principal_object_id" {
  description = "Deployment principal object ID used by this module."
  value       = var.deployment_principal_object_id
}