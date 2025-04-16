terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
    }
    azuredevops = {
      source = "microsoft/azuredevops"
    }
  }
}

provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
  client_id       = var.client_id
  client_secret   = var.client_secret
  tenant_id       = var.tenant_id
}

provider "azuredevops" {
  org_service_url = "https://dev.azure.com/shuntagami"
  # Personal Access Token認証を使用する
}
