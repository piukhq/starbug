"""Module providing functions for interacting with Azure."""

from azure.identity import DefaultAzureCredential
from azure.mgmt.msi import ManagedServiceIdentityClient
from loguru import logger

from starbug.settings import oidc_settings


class AzureOIDC:
    """Add/Removes the requested namespace to an Azure Managed Identity object for OIDC Calls."""

    def __init__(self, namespace: str | None = None) -> None:
        """Initialize the AzureOIDC class.

        Args:
            namespace (str | None, optional): The namespace to add to the Managed Identity. Defaults to None.

        """
        self.namespace = namespace
        self.resource_group_name = oidc_settings.resource_group_name
        self.subscription_id = oidc_settings.subscription_id
        self.identities = oidc_settings.identities
        self.issuer_url = oidc_settings.issuer_url
        self.credential = DefaultAzureCredential()
        self.client = ManagedServiceIdentityClient(self.credential, self.subscription_id)

    def setup_federated_credentials(self) -> None:
        """Create Federated Identity Credentials for all Managed Identities."""
        if not self.namespace:
            return
        for identity in self.identities:
            logger.info(f"Creating Federated Identity Credentials for {self.namespace}-{identity}")
            self.client.federated_identity_credentials.create_or_update(
                resource_group_name=self.resource_group_name,
                resource_name=f"{self.resource_group_name}-{identity}",
                federated_identity_credential_resource_name=f"{self.namespace}-{identity}",
                parameters={
                    "properties": {
                        "audiences": ["api://AzureADTokenExchange"],
                        "issuer": self.issuer_url,
                        "subject": f"system:serviceaccount:{self.namespace}:{identity}",
                    },
                },
            )

    def remove_federated_credentials(self) -> None:
        """Remove Federated Identity Credentials for all Managed Identities."""
        if not self.namespace:
            return
        for identity in self.identities:
            logger.info(f"Removing Federated Identity Credentials for {self.namespace}-{identity}")
            self.client.federated_identity_credentials.delete(
                resource_group_name=self.resource_group_name,
                resource_name=f"{self.resource_group_name}-{identity}",
                federated_identity_credential_resource_name=f"{self.namespace}-{identity}",
            )

    def cleanup_federated_credentials(self) -> None:
        """Look for and remove any Federated Identity Credentials for all Managed Identities."""
        for identity in self.identities:
            for credential in self.client.federated_identity_credentials.list(
                resource_group_name=self.resource_group_name,
                resource_name=f"{self.resource_group_name}-{identity}",
            ):
                if credential.name.startswith(tuple(oidc_settings.ignored_prefixes)):
                    continue
                logger.info(f"Removing Federated Identity Credential {credential.name}")
                self.client.federated_identity_credentials.delete(
                    resource_group_name=self.resource_group_name,
                    resource_name=f"{self.resource_group_name}-{identity}",
                    federated_identity_credential_resource_name=credential.name,
                )
