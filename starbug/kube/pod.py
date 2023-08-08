"""Base Models for Kubernetes Pods."""

from starbug.kube.common import KubernetesModel


class Tolerations(KubernetesModel):
    """Defines Tolerations for a Kubernetes Pod Object."""

    key: str = "kubernetes.azure.com/scalesetpriority"
    operator: str = "Equal"
    value: str = "spot"
    effect: str = "NoSchedule"

class ImagePullSecrets(KubernetesModel):
    """Defines imagePullSecrets for a Kubernetes Pod Object."""

    name: str

class EnvironmentVariable(KubernetesModel):
    """Defines Environment Variables for use within a Container."""

    name: str
    value: str

class Container(KubernetesModel):
    """Defines a Container for use within a Kubernetes Pod Spec."""

    args: list[str] | None = None
    command: list[str] | None = None
    env: list[EnvironmentVariable] | None = None
    image: str
    image_pull_policy: str = "Always"
    name: str = "app"
