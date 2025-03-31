from azure.storage.blob.aio import BlobServiceClient
from chainlit.data.storage_clients.azure_blob import AzureBlobStorageClient
import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

from app.config import config

def setup_azure_storage():
    """
    Sets up Azure Blob Storage for Chainlit and applies monkey patches for Azurite compatibility.
    """
    # Apply monkey patch for Azurite compatibility
    _apply_azurite_monkey_patch()
    
    # Configure storage client
    storage_client = AzureBlobStorageClient(
        container_name=config.BLOB_CONTAINER_NAME,
        storage_account=config.AZURE_STORAGE_ACCOUNT,
        storage_key=config.AZURE_STORAGE_KEY,
    )
    
    # Initialize data layer
    cl_data._data_layer = SQLAlchemyDataLayer(
        conninfo=config.ASYNC_DATABASE_URL, 
        storage_provider=storage_client
    )

def _apply_azurite_monkey_patch():
    """
    Applies monkey patch to BlobServiceClient for Azurite compatibility.
    Modifies connection strings to work with local Azurite emulator.
    """
    original_from_connection_string = BlobServiceClient.from_connection_string
    
    def patched_from_connection_string(connection_string, **kwargs):
        # Modify connection for Azurite emulator
        if "devstoreaccount1" in connection_string:
            # Change HTTPS to HTTP
            connection_string = connection_string.replace(
                "DefaultEndpointsProtocol=https", 
                "DefaultEndpointsProtocol=http"
            )
            
            # Add or update endpoint
            if "EndpointSuffix" in connection_string:
                connection_string = connection_string.replace(
                    "EndpointSuffix=core.windows.net", 
                    "BlobEndpoint=http://azurite:10000/devstoreaccount1"
                )
            else:
                connection_string += ";BlobEndpoint=http://azurite:10000/devstoreaccount1"

        return original_from_connection_string(connection_string, **kwargs)
    
    # Apply the monkey patch
    BlobServiceClient.from_connection_string = patched_from_connection_string