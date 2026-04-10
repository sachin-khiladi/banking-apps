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
    use_azuread_auth     = true
    use_oidc             = true
  }
}

provider "azurerm" {
  resource_provider_registrations = "none"
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
