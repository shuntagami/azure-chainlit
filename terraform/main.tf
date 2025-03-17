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

    # ヘルスチェックの設定
    health_check_path                 = "/api/health"
    health_check_eviction_time_in_min = 2
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
}

# PostgreSQL Database
resource "azurerm_postgresql_flexible_server_database" "this" {
  name      = "chainlit"
  server_id = azurerm_postgresql_flexible_server.this.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# PostgreSQL Firewall Rule - Allow Azure Services
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.this.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0" # This special value allows Azure services to access the server
}
