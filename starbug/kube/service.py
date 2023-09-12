"""Base Models for Kubernetes Services."""

from starbug.kube.common import KubernetesModel, Labels


class ServiceMetadata(KubernetesModel):
    """Defines the Metadata for a Kubernetes Service Object."""

    labels: Labels
    name: str
    namespace: str


class ServicePort(KubernetesModel):
    """Defines a Port for a Kubernetes Service Object."""

    port: int
    protocol: str = "TCP"
    target_port: int


class ServiceSpec(KubernetesModel):
    """Defines the Spec for a Kubernetes Service Object."""

    ports: list[ServicePort]
    selector: Labels


class Service(KubernetesModel):
    """Defines a Kubernetes Service Object."""

    api_version: str = "v1"
    kind: str = "Service"
    metadata: ServiceMetadata
    spec: ServiceSpec


def example() -> dict:
    """Provide an example Service Object."""
    s = Service(
        metadata=ServiceMetadata(
            name="jeff",
            namespace="jeffspace",
            labels={"aaa": "bbb"},
        ),
        spec=ServiceSpec(
            ports=[ServicePort(port=6502, target_port=6502)],
            selector={"aaa": "bbb"},
        ),
    )
    print(s.model_dump(by_alias=True))  # noqa: T201
