# ===========================================================================
# Module: storage_account
# Provisions: Azure Storage Account (StorageV2)
# ===========================================================================

locals {
  app_name_sanitized = lower(var.app_name)
  env_sanitized      = lower(var.env)

  storage_account_name = "st${local.app_name_sanitized}${local.env_sanitized}${var.unique_suffix}"
}

resource "azurerm_storage_account" "main" {
  name                = local.storage_account_name
  resource_group_name = var.resource_group_name
  location            = var.location

  account_tier             = var.account_tier
  account_replication_type = var.account_replication_type
  account_kind             = "StorageV2"
  access_tier              = var.access_tier

  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = var.allow_blob_public_access
  is_hns_enabled                  = var.enable_hns

  tags = var.tags

  lifecycle {
    precondition {
      condition     = length(local.storage_account_name) >= 3 && length(local.storage_account_name) <= 24
      error_message = "storage_account_name must be between 3 and 24 characters. Got: \"${local.storage_account_name}\"."
    }
  }
}
