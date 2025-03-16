output "app_url" {
  description = "The URL of the deployed Chainlit application"
  value       = "https://${azurerm_linux_web_app.this.default_hostname}"
}

output "acr_login_server" {
  description = "The login server of the Azure Container Registry"
  value       = azurerm_container_registry.this.login_server
}

output "acr_admin_username" {
  description = "The admin username for the Azure Container Registry"
  value       = azurerm_container_registry.this.admin_username
}

output "resource_group_name" {
  description = "The name of the resource group"
  value       = azurerm_resource_group.this.name
}
