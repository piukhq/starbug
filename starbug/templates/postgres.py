"""Postgres Application Kubernetes Objects."""

from starbug.kube.deployment import (
    Deployment,
    DeploymentContainer,
    DeploymentEnv,
    DeploymentMetadata,
    DeploymentSelector,
    DeploymentSpec,
    DeploymentTemplate,
    DeploymentTemplateMetadata,
    DeploymentTemplateSpec,
)
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
            metadata=DeploymentMetadata(
                labels=self.labels,
                namespace=self.namespace,
                name=self.name,
            ),
            spec=DeploymentSpec(
                selector=DeploymentSelector(match_labels=self.labels),
                template=DeploymentTemplate(
                    metadata=DeploymentTemplateMetadata(labels=self.labels),
                    spec=DeploymentTemplateSpec(
                        containers=[
                            DeploymentContainer(
                                image="docker.io/postgres:14",
                                env=[
                                    DeploymentEnv(
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
