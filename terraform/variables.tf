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

# env var used in the app
variable "openai_api_key" {
  description = "The API key for the OpenAI API"
  type        = string
  sensitive   = true
}

variable "openai_api_version" {
  description = "The version of the OpenAI API"
  type        = string
  default     = "2025-02-01-preview"
}

variable "azure_openai_endpoint" {
  description = "The endpoint for the Azure OpenAI API"
  type        = string
  sensitive   = true
}

variable "postgresql_server_name" {
  description = "The name of the PostgreSQL server"
  type        = string
  default     = "psql-chainlit"
}

variable "postgresql_admin_username" {
  description = "The administrator username for the PostgreSQL server"
  type        = string
  default     = "postgres"
}

variable "postgresql_database_name" {
  description = "The name of the PostgreSQL database"
  type        = string
}

variable "postgresql_admin_password" {
  description = "The administrator password for the PostgreSQL server"
  type        = string
  sensitive   = true
}

variable "azure_storage_account_name" {
  description = "The name of the Azure Storage Account"
  type        = string
  default     = "devstoreaccount1"
}

variable "azure_storage_account_key" {
  description = "The access key for the Azure Storage Account"
  type        = string
  default     = "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
  sensitive   = true
}

variable "blob_container_name" {
  description = "The name of the Blob Container"
  type        = string
  default     = "shuntagami-chainlit-app"
}

variable "chainlit_auth_secret" {
  description = "The secret for the Chainlit Auth"
  type        = string
  sensitive   = true
}
