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
    WEBSITES_PORT  = "8000"
    OPENAI_API_KEY = var.openai_api_key
    OPENAI_API_VERSION = var.openai_api_version
    AZURE_OPENAI_ENDPOINT = var.azure_openai_endpoint
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
