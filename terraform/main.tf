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
    container_registry_use_managed_identity = true

    # Dockerイメージの指定 (ACRのログインサーバーを使う)
    application_stack {
      docker_image_name = "${azurerm_container_registry.this.login_server}/${var.docker_image_name}:${var.docker_image_tag}"
    }

    always_on  = true
    ftps_state = "Disabled"
  }

  # すでにマネージドIDを使うのであれば、DOCKER_REGISTRY_SERVER_USERNAMEやPASSWORDは不要。
  # ただし環境変数として参照する場合は別ですが、イメージPull目的であれば削除してOK。
  app_settings = {
    "WEBSITES_PORT" = "8081"
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


# ACRが完全に作成された後にDockerイメージをビルド・プッシュする
# resource "null_resource" "docker_build_push" {
#   depends_on = [azurerm_container_registry.this]

#   # リソースグループやACRの名前が変更されたとき、またはDockerfileが変更されたときに再実行
#   triggers = {
#     acr_id = azurerm_container_registry.this.id
#     # 必要に応じてDockerfileのハッシュ値を追加することも可能
#     # dockerfile_hash = filemd5("${path.module}/../Dockerfile")
#   }

#   provisioner "local-exec" {
#     command = <<-EOT
#       az login --service-principal -u ${var.client_id} -p ${var.client_secret} --tenant ${var.tenant_id}
#       az acr login --name ${azurerm_container_registry.this.name}

#       # ローカルビルド＆プッシュの場合
#       docker build -t ${azurerm_container_registry.this.login_server}/${var.docker_image_name}:${var.docker_image_tag} -f ../Dockerfile ..
#       docker push ${azurerm_container_registry.this.login_server}/${var.docker_image_name}:${var.docker_image_tag}

#       # または、ACR Tasksを使用する場合（コメントアウトを外す）
#       # cd .. && az acr build --registry ${azurerm_container_registry.this.name} --image ${var.docker_image_name}:${var.docker_image_tag} --file Dockerfile .
#     EOT
#   }
# }

# イメージがプッシュされた後にWebアプリを更新する
# これにより、新しいイメージが確実にデプロイされる
# resource "null_resource" "restart_webapp" {
#   depends_on = [
#     azurerm_linux_web_app.this,
#     azurerm_role_assignment.acr_pull,
#     null_resource.docker_build_push
#   ]

#   triggers = {
#     # DockerイメージビルドリソースのIDを監視
#     docker_build_id = null_resource.docker_build_push.id
#   }

#   provisioner "local-exec" {
#     command = <<-EOT
#       az login --service-principal -u ${var.client_id} -p ${var.client_secret} --tenant ${var.tenant_id}
#       az webapp restart --name ${azurerm_linux_web_app.this.name} --resource-group ${azurerm_resource_group.this.name}
#     EOT
#   }
# }
