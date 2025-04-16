# Database Migration Guide for Chainlit Application

This guide describes how to set up and use the automated database migration pipeline for the Chainlit application using Azure DevOps and Alembic.

## Overview

The database migration process is automated using Azure DevOps pipelines. We use Alembic to manage database schema migrations, allowing for:

- Version-controlled database schema changes
- Ability to upgrade or downgrade to specific versions
- Manual triggering of migrations separate from application deployments

## Prerequisites

1. **Azure Subscription** with appropriate permissions
2. **Azure DevOps Organization** access with permissions to create projects and pipelines
3. **Service Principal** with access to required Azure resources
4. **Terraform** installed locally for infrastructure provisioning (version 1.0+)

## Setting Up the Environment

### 1. Configure Terraform Variables

Update your terraform.tfvars file with the required values:

```
# General Azure settings
azure_subscription_id       = "your-subscription-id"
azure_subscription_name     = "your-subscription-name"
azure_tenant_id             = "your-tenant-id"
azure_service_principal_id  = "your-service-principal-id"
azure_service_principal_key = "your-service-principal-secret"

# Database settings
db_host     = "your-postgresql-server-name.postgres.database.azure.com"
db_name     = "your-database-name"
db_username = "your-database-username"
db_password = "your-database-password"

# Azure DevOps settings
azure_devops_project_name   = "Chainlit-App"
```

### 2. Deploy Infrastructure with Terraform

```bash
# Initialize Terraform
terraform init

# Plan the changes
terraform plan -out=tfplan

# Apply the changes
terraform apply tfplan
```

### 3. Set Up Azure DevOps Pipeline

The Terraform deployment will create:

- Azure DevOps project
- Git repository
- Variable group with database credentials
- Pipeline definition

After deployment:

1. Clone the newly created Git repository
2. Copy your application code into the repository
3. Push the code, including the `azure-pipelines/db-migration-pipeline.yml` file

## Using the Migration Pipeline

### Running Migrations Through the Azure DevOps UI

1. Navigate to the Azure DevOps project created by Terraform
2. Go to Pipelines > Pipelines
3. Select the "Database-Migration-Pipeline"
4. Click "Run Pipeline"
5. Configure the parameters:
   - **Migration Target**: Choose from `head` (latest), `base` (reset), or `custom` (specific version)
   - **Custom Migration Target**: If using `custom`, specify the migration identifier or relative steps (e.g., `+2`, `-1`)
   - **Show SQL Statements**: Enable to preview SQL without applying changes
6. Click "Run" to start the migration process

### Understanding Pipeline Stages

The pipeline consists of two main stages:

1. **Validate Migration**: Performs pre-checks without applying changes
   - Verifies Alembic configuration
   - Optionally displays SQL that would be executed
2. **Deploy Migration**: Applies the actual database changes
   - Shows current migration version before changes
   - Applies migrations to the target version
   - Verifies the new migration version

### Creating New Migrations

To create new migrations, follow the standard Alembic workflow:

```bash
# Navigate to the app directory
cd app

# Create a new migration
alembic revision -m "description_of_changes"

# Edit the generated migration file in migrations/versions/
# Add your upgrade() and downgrade() implementation

# Test locally before committing
alembic upgrade head
```

After testing, commit and push your changes to the repository.

## Troubleshooting

### Common Issues

1. **Connection Errors**:

   - Verify database credentials in the variable group
   - Check network access permissions for Azure services

2. **Permission Issues**:

   - Ensure the service principal has appropriate permissions
   - Verify database user permissions for schema changes

3. **Migration Conflicts**:
   - If you encounter conflicts between branches, resolve them by creating a new migration that reconciles the changes

### Viewing Logs

Detailed logs are available in the Azure DevOps pipeline run:

1. Navigate to the pipeline run
2. Click on the specific job to view detailed logs
3. Use the `alembic history` and `alembic current` outputs to understand migration state

## Best Practices

1. **Test Migrations Locally** before pushing to the repository
2. **Use Descriptive Migration Names** that clearly indicate the purpose
3. **Include Both Upgrade and Downgrade** logic in migrations
4. **Consider Data Migration** needs alongside schema changes
5. **Run Migrations During Low-Traffic Periods** to minimize impact

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Azure DevOps Pipelines Documentation](https://docs.microsoft.com/en-us/azure/devops/pipelines/?view=azure-devops)
- [Terraform Azure DevOps Provider](https://registry.terraform.io/providers/microsoft/azuredevops/latest/docs)
