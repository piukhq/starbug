"""Redis Application Kubernetes Objects."""

from starbug.kube.common import Metadata
from starbug.kube.deployment import (
    Deployment,
    DeploymentSelector,
    DeploymentSpec,
    DeploymentTemplate,
    DeploymentTemplateSpec,
)
from starbug.kube.pod import Container
from starbug.kube.service import Service, ServiceMetadata, ServicePort, ServiceSpec
from starbug.kube.serviceaccount import ServiceAccount, ServiceAccountMetadata


class Redis:
    """Defines a Redis Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Redis Class."""
        self.namespace = namespace
        self.name = "redis"
        self.image = "docker.io/redis:6" if image is None else image
        self.labels = {"app": "redis"}
        self.serviceaccount = ServiceAccount(
            metadata=ServiceAccountMetadata(name=self.name, namespace=self.namespace),
        )
        self.service = Service(
            metadata=ServiceMetadata(name=self.name, namespace=self.namespace, labels=self.labels),
            spec=ServiceSpec(ports=[ServicePort(port=6379, target_port=6379)], selector=self.labels),
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
                            Container(image=self.image),
                        ],
                        service_account_name=self.serviceaccount.metadata.name,
                    ),
                ),
            ),
        )

    def __iter__(self) -> list:
        """Return all Objects as a list."""
        yield from [self.serviceaccount, self.service, self.deployment]
