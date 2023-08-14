"""Postgres Application Kubernetes Objects."""

from starbug.kube.common import Metadata
from starbug.kube.deployment import (
    Deployment,
    DeploymentSelector,
    DeploymentSpec,
    DeploymentTemplate,
    DeploymentTemplateSpec,
)
from starbug.kube.pod import Container, EnvironmentVariable
from starbug.kube.service import Service, ServiceMetadata, ServicePort, ServiceSpec
from starbug.kube.serviceaccount import ServiceAccount, ServiceAccountMetadata


class Postgres:
    """Defines a Postgres Instance."""

    def __init__(self, namespace: str) -> None:
        """Initialize the Postgres Class."""
        self.namespace = namespace
        self.name = "postgres"
        self.labels = {"app": "postgres"}
        self.serviceaccount = ServiceAccount(
            metadata=ServiceAccountMetadata(name=self.name, namespace=self.namespace),
        )
        self.service = Service(
            metadata=ServiceMetadata(name=self.name, namespace=self.namespace, labels=self.labels),
            spec=ServiceSpec(ports=[ServicePort(port=5432, target_port=5432)], selector=self.labels),
        )
        self.deployment = Deployment(
            metadata=Metadata(
                labels=self.labels,
                namespace=self.namespace,
                name=self.name,
            ),
            spec=DeploymentSpec(
                selector=DeploymentSelector(match_labels=self.labels),
                template=DeploymentTemplate(
                    metadata=Metadata(labels=self.labels),
                    spec=DeploymentTemplateSpec(
                        containers=[
                            Container(
                                image="docker.io/postgres:14",
                                env=[
                                    EnvironmentVariable(
                                        name="POSTGRES_HOST_AUTH_METHOD",
                                        value="trust",
                                    ),
                                ],
                            ),
                        ],
                        service_account_name=self.serviceaccount.metadata.name,
                    ),
                ),
            ),
        )

    def __iter__(self) -> list:
        """Return all Objects as a list."""
        yield from [self.serviceaccount, self.service, self.deployment]
