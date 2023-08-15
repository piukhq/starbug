"""Base Models for Kubernetes Namespaces."""

import random
import string

from pydantic import Field

from starbug.kube.common import KubernetesModel


class NamespaceMetadata(KubernetesModel):
    """Defines Metadata for a Kubernetes Namespace Object."""

    name: str = Field(
        default_factory=lambda: f"starbug-test-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}",  # noqa: S311
    )
    annotations: dict[str, str] = {"linkerd.io/inject": "enabled"}  # noqa: RUF012


class Namespace(KubernetesModel):
    """Defines a Kubernetes Namespace Object."""

    api_version: str = "v1"
    kind: str = "Namespace"
    metadata: NamespaceMetadata = Field(default_factory=NamespaceMetadata)


def example() -> dict:
    """Provide an example Namespace Object."""
    n = Namespace()
    print(n.model_dump(by_alias=True))  # noqa: T201
