# Module: storage_account

Provisions an Azure Storage Account (StorageV2) with secure defaults.

## Resources Created

- `azurerm_storage_account` — storage account for application data or blobs

## Usage

```hcl
module "storage_account" {
  source = "../../modules/storage_account"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  app_name            = local.app_name
  env                 = var.env
  unique_suffix       = local.unique_suffix
  tags                = local.common_tags
}
```

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| resource_group_name | string | ✅ | Name of the resource group to deploy into. |
| location | string | ✅ | Azure region for all resources in this module. |
| app_name | string | ✅ | Short application name used as a naming prefix. |
| env | string | ✅ | Deployment environment (dev \| staging \| prod). |
| unique_suffix | string | ✅ | 6-character suffix for globally unique resource names. |
| account_tier | string | ❌ | Storage account tier: Standard \| Premium. |
| account_replication_type | string | ❌ | Replication: LRS \| GRS \| RAGRS \| ZRS \| GZRS \| RAGZRS. |
| access_tier | string | ❌ | Access tier for Blob Storage: Hot \| Cool. |
| enable_hns | bool | ❌ | Enable hierarchical namespace (Data Lake Storage Gen2). |
| allow_blob_public_access | bool | ❌ | Allow public access to blobs. |
| tags | map(string) | ❌ | Tags applied to all resources in this module. |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| id | string | Resource ID of the Storage Account. |
| name | string | Storage Account name. |
| primary_blob_endpoint | string | Primary Blob endpoint for the Storage Account. |
