"""Base Models for Kubernetes Service Accounts."""

from starbug.kube.common import KubernetesModel


class ServiceAccountMetadata(KubernetesModel):
    """Defines Metadata for a Kuberentes Service Account Object."""

    name: str
    namespace: str


class ServiceAccount(KubernetesModel):
    """Defines a Kubernetes Service Account Object."""

    api_version: str = "v1"
    kind: str = "ServiceAccount"
    metadata: ServiceAccountMetadata


def example() -> dict:
    """Provide an example Service Account Object."""
    s = ServiceAccount(metadata=ServiceAccountMetadata(name="jeff", namespace="default"))
    print(s.model_dump(by_alias=True))  # noqa: T201
