"""Base Models for Kubernetes Jobs."""
from starbug.kube.common import KubernetesModel, Labels, Metadata
from starbug.kube.pod import Container, ImagePullSecrets, PodVolume, Tolerations


class JobTemplateSpec(KubernetesModel):
    containers: list[Container]
    init_containers: list[Container] | None = None
    volumes: list[PodVolume] | None = None
    node_selector: dict[str, str] | None = {"kubernetes.azure.com/scalesetpriority": "spot"}  # noqa: RUF012
    tolerations: list[Tolerations] | None = [Tolerations(default_factory=Tolerations)]  # noqa: RUF012
    image_pull_secrets: list[ImagePullSecrets] | None = None
    service_account_name: str | None = None
    restart_policy: str = "Never"


class JobTemplate(KubernetesModel):
    spec: JobTemplateSpec


class JobSpec(KubernetesModel):
    template: JobTemplate
    backoff_limit: int = 0


class Job(KubernetesModel):
    api_version: str = "batch/v1"
    kind: str = "Job"
    metadata: Metadata
    spec: JobSpec


def example() -> None:
    j = Job(
        metadata=Metadata(
            name="example-job",
            namespace="default",
            labels=Labels(
                {"app": "example"},
            ),
        ),
        spec=JobSpec(
            backoff_limit=4,
            template=JobTemplate(
                spec=JobTemplateSpec(
                    containers=[
                        Container(image="debian:12", command=["sleep", "60"]),
                    ],
                    restart_policy="Never",
                ),
            ),
        ),
    )
    print(j.model_dump(exclude_none=True, by_alias=True))  # noqa: T201


if __name__ == "__main__":
    example()
