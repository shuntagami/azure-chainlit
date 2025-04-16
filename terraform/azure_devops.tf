# Azure DevOps Project
resource "azuredevops_project" "project" {
  name               = var.azure_devops_project_name
  description        = "Project for managing Chainlit application and database migrations"
  visibility         = "private"
  version_control    = "Git"
  work_item_template = "Agile"
}

# Variable Group for Database Credentials
resource "azuredevops_variable_group" "db_credentials" {
  project_id   = azuredevops_project.project.id
  name         = "DatabaseCredentials"
  description  = "Database credentials for migration pipeline"
  allow_access = true

  variable {
    name  = "APP_DATABASE_HOST"
    value = var.postgresql_server_name
  }

  variable {
    name  = "APP_DATABASE_NAME"
    value = var.postgresql_database_name
  }

  variable {
    name  = "APP_DATABASE_USERNAME"
    value = var.postgresql_admin_username
  }

  variable {
    name         = "APP_DATABASE_PASSWORD"
    secret_value = var.postgresql_admin_password
    is_secret    = true
  }
}

# Service Connection for Azure
resource "azuredevops_serviceendpoint_azurerm" "azure_service_connection" {
  project_id            = azuredevops_project.project.id
  service_endpoint_name = "AzureServiceConnection"
  description           = "Connection to Azure for the Chainlit application"

  credentials {
    serviceprincipalid  = var.client_id
    serviceprincipalkey = var.client_secret
  }

  azurerm_spn_tenantid      = var.tenant_id
  azurerm_subscription_id   = var.subscription_id
  azurerm_subscription_name = var.subscription_name
}

# Azure DevOps Git Repository
resource "azuredevops_git_repository" "repo" {
  project_id = azuredevops_project.project.id
  name       = "azure-chainlit"
  initialization {
    init_type = "Clean"
  }
}

# Build Definition (Pipeline) for Database Migration
resource "azuredevops_build_definition" "migration_pipeline" {
  project_id = azuredevops_project.project.id
  name       = "Database-Migration-Pipeline"
  path       = "\\Pipelines"

  repository {
    repo_type   = "TfsGit"
    repo_id     = azuredevops_git_repository.repo.id
    branch_name = "main"
    yml_path    = "azure-pipelines/db-migration-pipeline.yml"
  }

  variable_groups = [
    azuredevops_variable_group.db_credentials.id
  ]

  variable {
    name  = "migrationTarget"
    value = "head"
  }
}
