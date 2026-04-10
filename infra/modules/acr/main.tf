# ===========================================================================
# Module: acr
# Provisions: Azure Container Registry + AcrPull role for the app UAMI
#
# The UAMI (created in the keyvault module) is granted AcrPull so the
# Container App can pull images without managing admin credentials.
# ACR Admin is intentionally disabled — RBAC-only access.
# ===========================================================================

resource "azurerm_container_registry" "acr" {
  # ACR names: alphanumeric only, 5-50 chars, globally unique.
  # Pattern: acr + <app_name> + <env> + <unique_suffix>
  # e.g. acrbankapidev c8775a  (19 chars)
  name                = "acr${var.app_name}${var.env}${var.unique_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.acr_sku

  # RBAC-only — no username/password admin access
  admin_enabled = false

  tags = var.tags
}

# ---------------------------------------------------------------------------
# RBAC — UAMI → AcrPull
# Allows the Container App's managed identity to pull images at runtime
# without needing admin credentials or a registry password.
# ---------------------------------------------------------------------------
resource "azurerm_role_assignment" "acr_pull_uami" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = var.uami_principal_id

  # The UAMI is a managed identity. Without this flag the AzureRM provider
  # polls AAD to confirm the principal exists — which can hang for hours when
  # a newly created managed identity hasn't fully propagated yet.
  skip_service_principal_aad_check = true

  # azurerm_role_assignment does not support in-place updates.
  # Do not use create_before_destroy here — Azure enforces uniqueness on
  # scope + role + principal, so replacement attempts can fail with
  # RoleAssignmentExists. Recovery from unexpected pre-existing assignments
  # must follow the operator runbook rather than adding import blocks to code.
  lifecycle {
    ignore_changes = [
      # skip_service_principal_aad_check is a Terraform-only flag that Azure
      # never persists. After provider drift or state refresh, the state reads
      # it back as null, which causes a perpetual "update" that AzureRM rejects
      # with "doesn't support update". Ignoring it prevents that cycle.
      skip_service_principal_aad_check,
      # role_definition_id is computed alongside role_definition_name and can
      # differ between provider versions without a real config change.
      role_definition_id,
    ]
  }
}

# ---------------------------------------------------------------------------
# RBAC — deploying principal → AcrPush
# Allows the CI/CD service-principal pipeline to push images via:
#   az acr login --name <acr_name>
#   docker push <acr_login_server>/bank-api:<tag>
# The deployer is a service principal in CI/CD; skip_service_principal_aad_check
# prevents the provider from polling AAD for propagation, which avoids
# intermittent 400/403 errors when the identity was recently created or
# re-granted.
# ---------------------------------------------------------------------------
resource "azurerm_role_assignment" "acr_push_deployer" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPush"
  principal_id         = var.deployer_object_id

  skip_service_principal_aad_check = true

  lifecycle {
    ignore_changes = [
      # Provider-only flag; Azure never persists it — ignore to prevent
      # perpetual "update" cycles after provider version changes.
      skip_service_principal_aad_check,
      # Computed alongside role_definition_name; may vary across provider
      # versions without a real config change.
      role_definition_id,
    ]
  }
}
