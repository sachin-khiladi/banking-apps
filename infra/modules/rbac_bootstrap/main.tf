# ===========================================================================
# Module: rbac_bootstrap
# Provisions: Resource-group scoped bootstrap RBAC for deployment principal
# ===========================================================================

resource "azurerm_role_assignment" "bootstrap" {
  for_each = var.enabled ? toset(var.role_definition_names) : toset([])

  scope                = var.resource_group_id
  role_definition_name = each.value
  principal_id         = var.deployment_principal_object_id

  # ABAC condition applied only to User Access Administrator to constrain which
  # roles the grantee may assign — prevents privilege escalation.
  # Requires uaa_condition to be non-null; null disables the condition.
  condition_version = each.value == "User Access Administrator" && var.uaa_condition != null ? "2.0" : null
  condition         = each.value == "User Access Administrator" && var.uaa_condition != null ? var.uaa_condition : null

  # Deployment principal is typically a service principal used by CI/CD.
  skip_service_principal_aad_check = var.skip_service_principal_aad_check

  lifecycle {
    ignore_changes = [
      # Provider-only flag can drift after provider refresh and should not trigger updates.
      skip_service_principal_aad_check,
      # Computed alongside role_definition_name and may vary by provider version.
      role_definition_id,
    ]
  }
}