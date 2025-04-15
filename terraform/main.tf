# リソースグループ
resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
}

# ACR (Azure Container Registry)
resource "azurerm_container_registry" "this" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku                 = "Basic"

  # マネージドIDを使うなら、管理者ユーザー (admin_enabled) は false でもOK
  # admin_enabled       = false
}

# Web App for Containers 用のApp Service Plan
resource "azurerm_service_plan" "this" {
  name                = var.app_service_plan_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  os_type             = "Linux"
  sku_name            = var.app_service_plan_sku
}

# Web App for Containers
resource "azurerm_linux_web_app" "this" {
  name                = var.app_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  service_plan_id     = azurerm_service_plan.this.id

  # システム割り当てマネージドIDを有効化
  identity {
    type = "SystemAssigned"
  }

  site_config {
    # ACRへのアクセスをマネージドIDで行う
    app_command_line                        = "chainlit run app.py --host 0.0.0.0 --port 8000"
    container_registry_use_managed_identity = true

    # Dockerイメージの指定 (ACRのログインサーバーを使う)
    application_stack {
      docker_image_name   = "${var.docker_image_name}:${var.docker_image_tag}"
      docker_registry_url = "https://${azurerm_container_registry.this.login_server}"
    }

    always_on = true
  }

  # すでにマネージドIDを使うのであれば、DOCKER_REGISTRY_SERVER_USERNAMEやPASSWORDは不要。
  # ただし環境変数として参照する場合は別ですが、イメージPull目的であれば削除してOK。
  app_settings = {
    WEBSITES_PORT         = "8000"
    OPENAI_API_KEY        = var.openai_api_key
    OPENAI_API_VERSION    = var.openai_api_version
    AZURE_OPENAI_ENDPOINT = var.azure_openai_endpoint
    APP_DATABASE_HOST     = azurerm_postgresql_flexible_server.this.fqdn
    APP_DATABASE_USERNAME = var.postgresql_admin_username
    APP_DATABASE_PASSWORD = var.postgresql_admin_password
    APP_DATABASE_NAME     = var.postgresql_database_name
    WEBSITES_SSH_ENABLED  = "true"
    AZURE_STORAGE_ACCOUNT = var.azure_storage_account_name
    AZURE_STORAGE_KEY     = azurerm_storage_account.this.primary_access_key
    BLOB_CONTAINER_NAME   = var.blob_container_name
    CHAINLIT_AUTH_SECRET  = var.chainlit_auth_secret
  }
}

# ACR に Web App のマネージドIDを「AcrPull」ロールで割り当てる
# これがないと "pull access denied" になるので注意
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.this.id
  role_definition_name = "AcrPull"

  # principal_id には、Web Appで有効になったマネージドIDのprincipal_idを指定
  principal_id = azurerm_linux_web_app.this.identity[0].principal_id
}

# PostgreSQL Server
resource "azurerm_postgresql_flexible_server" "this" {
  name                = var.postgresql_server_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  sku_name   = "B_Standard_B1ms" # Basic tier
  storage_mb = 32768             # 32GB

  backup_retention_days        = 7
  geo_redundant_backup_enabled = false

  administrator_login    = var.postgresql_admin_username
  administrator_password = var.postgresql_admin_password
  version                = "14"

  zone = "1" # 可用性ゾーン

  # 高可用性が必要な場合は以下を有効化
  # high_availability {
  #   mode = "ZoneRedundant"
  # }

  # PostgreSQLサーバーの環境変数設定
  # 注: PostgreSQL Flexible Serverでは直接環境変数を設定するリソースはありません
  # 必要な設定はパラメータ設定で行います
  # 例: postgresql.conf の設定を変更したい場合は以下のようなリソースを追加します
  # azurerm_postgresql_flexible_server_configuration を使用
  authentication {
    active_directory_auth_enabled = true
    tenant_id                     = var.tenant_id
  }
}

# PostgreSQL Database
resource "azurerm_postgresql_flexible_server_database" "this" {
  name      = var.postgresql_database_name
  server_id = azurerm_postgresql_flexible_server.this.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_active_directory_administrator" "app" {
  server_name         = azurerm_postgresql_flexible_server.this.name
  resource_group_name = azurerm_resource_group.this.name
  tenant_id           = var.tenant_id
  principal_name      = azurerm_linux_web_app.this.name
  principal_type      = "ServicePrincipal"
  object_id           = azurerm_linux_web_app.this.identity[0].principal_id
}

# PostgreSQL Firewall Rule - Allow Azure Services
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.this.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0" # This special value allows Azure services to access the server
}

# Azure Storage Account
resource "azurerm_storage_account" "this" {
  name                     = var.azure_storage_account_name
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "this" {
  name                  = var.blob_container_name
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}
