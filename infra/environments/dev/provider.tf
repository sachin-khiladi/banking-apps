# ===========================================================================
# environments/dev — Terraform + Provider + Backend
# Backend key is hardcoded here so this environment is independently
# deployable without any -backend-config flag.
# ===========================================================================
terraform {
  required_version = ">= 1.6"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.1"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-tf-backend"
    storage_account_name = "strgtfbackendb86177"
    container_name       = "bank-api-tfstate"
    key                  = "bankapi-dev-tf.tfstate"
  }
}

provider "azurerm" {
  resource_provider_registrations = "none"
  subscription_id                 = "b86177f7-23c4-4a3a-b37f-5c4c8775af34"
  tenant_id                       = "47f8c7cd-1273-45b1-85c6-61d06e329024"
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}
