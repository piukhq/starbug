from os import getenv

from starbug.kube.common import Metadata
from starbug.kube.deployment import (
    Deployment,
    DeploymentSelector,
    DeploymentSpec,
    DeploymentTemplate,
    DeploymentTemplateSpec,
)
from starbug.kube.job import Job, JobSpec, JobTemplate, JobTemplateSpec
from starbug.kube.namespace import Namespace
from starbug.kube.pod import Container, ContainerPort, EnvironmentVariable, ImagePullSecrets
from starbug.kube.service import Service, ServiceMetadata, ServicePort, ServiceSpec
from starbug.kube.serviceaccount import ServiceAccount, ServiceAccountMetadata


class Kiroshi:
    """Define a Kiroshi Instance."""

    def __init__(self, namespace: Namespace, image: str | None = None) -> None:
        """Initialize the Kiroshi class."""
        self.namespace = namespace
        self.name = "kiroshi"
        self.image = "binkcore.azurecr.io/kiroshi:prod" if image is None else image
        self.labels = {"app": "kiroshi"}
        self.environment_variables = [
            EnvironmentVariable(
                name="blob_storage_account_dsn",
                value=str(getenv("AZURE_STORAGE_BLOB_DSN")),
            ),
            EnvironmentVariable(
                name="database_dsn",
                value="postgresql://postgres@postgres:5432/postgres",
            ),
        ]
        self.image_pull_secrets = [ImagePullSecrets(name="binkcore.azurecr.io")]
        self.serviceaccount = ServiceAccount(
            metadata=ServiceAccountMetadata(name=self.name, namespace=self.namespace),
        )
        self.migrator = Job(
            metadata=Metadata(
                labels=self.labels,
                name=self.name + "-migrator",
                namespace=self.namespace,
            ),
            spec=JobSpec(
                backoff_limit=10,
                template=JobTemplate(
                    spec=JobTemplateSpec(
                        restart_policy="OnFailure",
                        containers=[
                            Container(
                                name="app",
                                command=["linkerd-await", "--shutdown", "--"],
                                args=["alembic", "upgrade", "head"],
                                env=self.environment_variables,
                                image=self.image,
                            ),
                        ],
                        image_pull_secrets=self.image_pull_secrets,
                        service_account_name=self.serviceaccount.metadata.name,
                    ),
                ),
            ),
        )
        self.service = Service(
            metadata=ServiceMetadata(name=self.name, namespace=self.namespace, labels=self.labels),
            spec=ServiceSpec(ports=[ServicePort(port=80, target_port=6502)], selector=self.labels),
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
                                image=self.image,
                                args=["kiroshi","server","image"],
                                env=self.environment_variables,
                                ports=[
                                    ContainerPort(
                                        name="http",
                                        container_port=6502,
                                        protocol="TCP",
                                    ),
                                ],
                            ),
                        ],
                        image_pull_secrets=self.image_pull_secrets,
                        service_account_name=self.serviceaccount.metadata.name,
                    ),
                ),
            ),
        )

    def __iter__(self) -> list:
        """Return all Objects as a list."""
        yield from [self.serviceaccount, self.migrator, self.service, self.deployment]
