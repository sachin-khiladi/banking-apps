# ===========================================================================
# Module: container_app
# Provisions: Container App Environment + Container App
# ===========================================================================

# ---------------------------------------------------------------------------
# Container App Environment — linked to Log Analytics
# ---------------------------------------------------------------------------
resource "azurerm_container_app_environment" "cae" {
  name                       = "cae-${var.app_name}-${var.env}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Container App
# ---------------------------------------------------------------------------
resource "azurerm_container_app" "app" {
  name                         = "ca-${var.app_name}-${var.env}"
  container_app_environment_id = azurerm_container_app_environment.cae.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  tags = var.tags

  # The CAE must be fully provisioned before the CA is created.
  # (container_app_environment_id already implies this, but explicit is safer
  # given Azure ARM's eventual consistency on environment readiness.)
  depends_on = [azurerm_container_app_environment.cae]

  # UAMI — used for Key Vault + App Config RBAC at runtime
  identity {
    type         = "UserAssigned"
    identity_ids = [var.uami_id]
  }

  # KV-backed secrets (pulled via UAMI; no plaintext in state)
  secret {
    name                = "appinsights-connection-string"
    key_vault_secret_id = var.appinsights_secret_versionless_id
    identity            = var.uami_id
  }

  secret {
    name                = "smtp-password"
    key_vault_secret_id = var.smtp_password_secret_versionless_id
    identity            = var.uami_id
  }

  # ---------------------------------------------------------------------------
  # ACR registry pull via UAMI
  # Added only when container_image is sourced from a private ACR.
  # The UAMI must have AcrPull role on the registry (granted by the acr module).
  # Set acr_login_server = null to skip this block (e.g. when using MCR).
  # ---------------------------------------------------------------------------
  dynamic "registry" {
    for_each = var.acr_login_server != null ? [1] : []
    content {
      server   = var.acr_login_server
      identity = var.uami_id
    }
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = var.app_name
      image  = var.container_image
      cpu    = var.container_cpu
      memory = var.container_memory

      # Secrets injected as env vars
      env {
        name        = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        secret_name = "appinsights-connection-string"
      }

      # Cosmos DB — app uses DefaultAzureCredential (RBAC), not a connection string
      env {
        name  = "COSMOS_ACCOUNT_URL"
        value = var.cosmos_account_url
      }
      env {
        name  = "COSMOS_DB_NAME"
        value = var.cosmos_db_name
      }

      # Non-secret configuration
      env {
        name  = "AZURE_APP_CONFIG_ENDPOINT"
        value = var.app_config_endpoint
      }
      env {
        name  = "AZURE_KEY_VAULT_URI"
        value = var.key_vault_uri
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = var.uami_client_id
      }
      env {
        name  = "ENVIRONMENT"
        value = var.env
      }
      env {
        name  = "SMTP_HOST"
        value = var.smtp_host
      }
      env {
        name  = "SMTP_PORT"
        value = tostring(var.smtp_port)
      }
      env {
        name  = "SMTP_USERNAME"
        value = var.smtp_username
      }
      env {
        name  = "SMTP_SENDER_EMAIL"
        value = var.smtp_sender_email
      }
      env {
        name  = "SMTP_USE_TLS"
        value = tostring(var.smtp_use_tls)
      }
      env {
        name  = "SMTP_TIMEOUT_SECONDS"
        value = tostring(var.smtp_timeout_seconds)
      }
      env {
        name        = "SMTP_PASSWORD"
        secret_name = "smtp-password"
      }

      liveness_probe {
        transport               = "HTTP"
        path                    = "/health"
        port                    = var.container_port
        initial_delay           = 10
        interval_seconds        = 30
        timeout                 = 5
        failure_count_threshold = 3
      }

      readiness_probe {
        transport               = "HTTP"
        path                    = "/health"
        port                    = var.container_port
        interval_seconds        = 10
        timeout                 = 5
        failure_count_threshold = 3
        success_count_threshold = 1
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = var.container_port
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}
