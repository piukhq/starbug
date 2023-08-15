from starbug.kube.common import Metadata
from starbug.kube.job import Job, JobSpec, JobTemplate, JobTemplateSpec
from starbug.kube.pod import Container, ImagePullSecrets


class BootstrapDB:
    """Defines a Bootstrap DB Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the BootstrapDB Class."""
        self.namespace = namespace
        self.name = "bootstrap-db"
        self.image = "binkcore.azurecr.io/ait-bootstrap-db:latest" if image is None else image
        self.labels = {"app": "bootstrap-db"}
        self.job = Job(
            metadata=Metadata(
                labels=self.labels,
                name=self.name,
                namespace=self.namespace,
            ),
            spec=JobSpec(
                template=JobTemplate(
                    spec=JobTemplateSpec(
                        containers=[
                            Container(
                                name="app",
                                image=self.image,
                            ),
                        ],
                        image_pull_secrets=[
                            ImagePullSecrets(name="binkcore.azurecr.io"),
                        ],
                    ),
                ),
            ),
        )

    def __iter__(self) -> list:
        """Return all Objects as a list."""
        yield from [self.job]
