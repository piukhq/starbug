"""Base Models for Kubernetes Pods."""

from starbug.kube.common import KubernetesModel, Metadata


class Secret(KubernetesModel):
    """Defines a Kubernetes Secret Object."""

    api_version: str = "v1"
    kind: str = "Secret"
    type: str = "Opaque"  # noqa: A003
    metadata: Metadata
    data: dict


def example() -> None:
    s = Secret(
        metadata=Metadata(
            name="jeff",
            namespace="default",
        ),
        data={
            "aaa": "bbb",
            "ccc": "ddd",
        },
    )
    print(s.model_dump(exclude_none=True, by_alias=True))  # noqa: T201


if __name__ == "__main__":
    example()
