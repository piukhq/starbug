"""Base Models for Kubernetes Pods."""

from pydantic import Field

from starbug.kube.common import KubernetesModel


class EmptyDir(KubernetesModel):
    """Defines an EmptyDir."""

    size_limit: str = "128Mi"

class PodVolume(KubernetesModel):
    """Defines a Pod Volume."""

    name: str = "reports"
    empty_dir: EmptyDir = Field(default_factory=EmptyDir)


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

class ContainerVolume(KubernetesModel):
    """Defines a Volume for use within a Container."""

    name: str = "reports"
    mount_path: str = "/mnt/reports"


class ContainerPort(KubernetesModel):
    """Defines Ports for use within a Container."""

    name: str
    container_port: int
    protocol: str


class Container(KubernetesModel):
    """Defines a Container for use within a Kubernetes Pod Spec."""

    args: list[str] | None = None
    command: list[str] | None = None
    env: list[EnvironmentVariable] | None = None
    image: str
    image_pull_policy: str = "Always"
    name: str = "app"
    ports: list[ContainerPort] | None = None
    volume_mounts: list[ContainerVolume] | None = None
