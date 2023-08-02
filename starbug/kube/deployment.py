"""Base Models for Kubernetes Deployments."""

from starbug.kube.common import KubernetesModel, Labels


class DeploymentSelector(KubernetesModel):
    """Defines the pod Selector for a Kubernetes Deployment Object."""

    match_labels: Labels


class DeploymentTemplateMetadata(KubernetesModel):
    """Defines Template Metadata for a Kubernetes Deployment Object."""

    labels: Labels


class DeploymentEnv(KubernetesModel):
    """Defines Environment vairbales for use within a Container."""

    name: str
    value: str


class DeploymentContainer(KubernetesModel):
    """Defines Specifications for a container within a Kubernetes Deployment Object."""

    args: list[str] | None = None
    command: list[str] | None = None
    env: list[DeploymentEnv] | None = None
    image: str
    image_pull_policy: str = "Always"
    name: str = "app"


class DeploymentImagePullSecrets(KubernetesModel):
    """Defines imagePullSecrets for a Kubernetes Deployment Object."""

    name: str


class DeploymentTemplateSpec(KubernetesModel):
    """Defines Specifications for a pod within a Kubernetes Deployment Object."""

    containers: list[DeploymentContainer]
    image_pull_secrets: list[DeploymentImagePullSecrets] | None = None
    service_account_name: str


class DeploymentTemplate(KubernetesModel):
    """Defines Template Specifications for a Kubernetes Deployment Object."""

    metadata: DeploymentTemplateMetadata
    spec: DeploymentTemplateSpec


class DeploymentMetadata(KubernetesModel):
    """Defines Metadata for a Kubernetes Deployment Object."""

    labels: Labels
    name: str
    namespace: str


class DeploymentSpec(KubernetesModel):
    """Defines Specifications for a Kubernetes Deployment Object."""

    replicas: int = 1
    selector: DeploymentSelector
    template: DeploymentTemplate


class Deployment(KubernetesModel):
    """Defines a Kubernetes Deployment Object."""

    api_version: str = "apps/v1"
    kind: str = "Deployment"
    metadata: DeploymentMetadata
    spec: DeploymentSpec


def example() -> dict:
    """Provide an example Deployment Object."""
    labels = {"foo": "bar"}
    d = Deployment(
        metadata=DeploymentMetadata(
            name="jeff",
            namespace="jeffspace",
            labels=labels,
        ),
        spec=DeploymentSpec(
            selector=DeploymentSelector(match_labels=labels),
            template=DeploymentTemplate(
                metadata=DeploymentTemplateMetadata(labels=labels),
                spec=DeploymentTemplateSpec(
                    containers=[
                        DeploymentContainer(
                            image="binkcore.azurecr.io/jeff:latest",
                            env=[
                                DeploymentEnv(name="aaa", value="bbb"),
                            ],
                        ),
                    ],
                    image_pull_secrets=[
                        DeploymentImagePullSecrets(name="jeffcorp.jafafactory.io"),
                    ],
                    service_account_name="jeff",
                ),
            ),
        ),
    )
    print(d.model_dump(exclude_none=True, by_alias=True))  # noqa: T201
