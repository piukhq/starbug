"""RabbitMQ Application Kubernetes Objects."""

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


class RabbitMQ:
    """Defines a RabbitMQ Instance."""

    def __init__(self, namespace: str) -> None:
        """Initialize the RabbitMQ Class."""
        self.namespace = namespace
        self.name = "rabbitmq"
        self.labels = {"app": "rabbitmq"}
        self.serviceaccount = ServiceAccount(
            metadata=ServiceAccountMetadata(name=self.name, namespace=self.namespace),
        )
        self.service = Service(
            metadata=ServiceMetadata(name=self.name, namespace=self.namespace, labels=self.labels),
            spec=ServiceSpec(ports=[ServicePort(port=5672, target_port=5672)], selector=self.labels),
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
                            Container(image="docker.io/rabbitmq:3"),
                        ],
                        service_account_name=self.serviceaccount.metadata.name,
                    ),
                ),
            ),
        )
        self.all = [self.serviceaccount, self.service, self.deployment]
