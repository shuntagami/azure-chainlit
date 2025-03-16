variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  sensitive   = true
}

variable "client_id" {
  description = "Azure Client ID (Service Principal)"
  type        = string
  sensitive   = true
}

variable "client_secret" {
  description = "Azure Client Secret (Service Principal)"
  type        = string
  sensitive   = true
}

variable "tenant_id" {
  description = "Azure Tenant ID"
  type        = string
  sensitive   = true
}

variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
  default     = "rg-chainlit-app"
}

variable "location" {
  description = "The Azure region where resources should be created"
  type        = string
  default     = "japaneast"
}

variable "app_service_plan_name" {
  description = "The name of the App Service Plan"
  type        = string
  default     = "asp-chainlit"
}

variable "app_service_plan_sku" {
  description = "The SKU name for the App Service Plan"
  type        = string
  default     = "B1" # Basic tier
}

variable "container_registry_name" {
  description = "The name of the Azure Container Registry"
  type        = string
  default     = "acrchaindlitapp" # アルファベット小文字と数字のみ
}

variable "app_name" {
  description = "The name of the Web App"
  type        = string
  default     = "app-chainlit"
}

variable "docker_image_name" {
  description = "The name of the Docker image"
  type        = string
  default     = "chainlit-app"
}

variable "docker_image_tag" {
  description = "The tag of the Docker image"
  type        = string
  default     = "latest"
}

variable "acr_name" {
  type        = string
  description = "The name of the Azure Container Registry"
  default     = "acrchainlitapp"
}
