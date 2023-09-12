"""Base Models for Kubernetes Deployments."""

from starbug.kube.common import KubernetesModel, Labels, Metadata
from starbug.kube.pod import Container, EnvironmentVariable, ImagePullSecrets, PodVolume, Tolerations


class DeploymentSelector(KubernetesModel):
    """Defines the pod Selector for a Kubernetes Deployment Object."""

    match_labels: Labels


class DeploymentTemplateSpec(KubernetesModel):
    """Defines Specifications for a pod within a Kubernetes Deployment Object."""

    containers: list[Container]
    volumes: list[PodVolume] | None = None
    node_selector: dict[str, str] | None = {"kubernetes.azure.com/scalesetpriority": "spot"}  # noqa: RUF012
    tolerations: list[Tolerations] | None = [Tolerations(default_factory=Tolerations)]  # noqa: RUF012
    image_pull_secrets: list[ImagePullSecrets] | None = None
    service_account_name: str | None = None


class DeploymentTemplate(KubernetesModel):
    """Defines Template Specifications for a Kubernetes Deployment Object."""

    metadata: Metadata
    spec: DeploymentTemplateSpec


class DeploymentSpec(KubernetesModel):
    """Defines Specifications for a Kubernetes Deployment Object."""

    replicas: int = 1
    selector: DeploymentSelector
    template: DeploymentTemplate


class Deployment(KubernetesModel):
    """Defines a Kubernetes Deployment Object."""

    api_version: str = "apps/v1"
    kind: str = "Deployment"
    metadata: Metadata
    spec: DeploymentSpec


def simple_deployment(
        name: str,
        namespace: str,
        labels: dict,
        image: str,
        ports: list | None = None,
        environment_variables: list | None = None,
        image_pull_secrets: list | None = None,
        service_account: str | None = None,
    ) -> Deployment:
    """Return a Deployment based on common critera."""
    return Deployment(
        metadata=Metadata(
            name=name,
            namespace=namespace,
            labels=labels,
        ),
        spec=DeploymentSpec(
            selector=DeploymentSelector(match_labels=labels),
            template=DeploymentTemplate(
                metadata=Metadata(labels=labels),
                spec=DeploymentTemplateSpec(
                    containers=[
                        Container(
                            image=image,
                            env=environment_variables,
                            ports=ports,
                        ),
                    ],
                    image_pull_secrets=image_pull_secrets,
                    service_account_name=service_account,
                ),
            ),
        ), 
    )

def example() -> dict:
    """Provide an example Deployment Object."""
    labels = {"foo": "bar"}
    d = Deployment(
        metadata=Metadata(
            name="jeff",
            namespace="jeffspace",
            labels=labels,
        ),
        spec=DeploymentSpec(
            selector=DeploymentSelector(match_labels=labels),
            template=DeploymentTemplate(
                metadata=Metadata(labels=labels),
                spec=DeploymentTemplateSpec(
                    node_selector=None,
                    tolerations=None,
                    containers=[
                        Container(
                            image="binkcore.azurecr.io/jeff:latest",
                            env=[
                                EnvironmentVariable(name="aaa", value="bbb"),
                            ],
                        ),
                    ],
                    image_pull_secrets=[
                        ImagePullSecrets(name="jeffcorp.jafafactory.io"),
                    ],
                    service_account_name="jeff",
                ),
            ),
        ),
    )
    print(d.model_dump(exclude_none=True, by_alias=True))  # noqa: T201


if __name__ == "__main__":
    example()
