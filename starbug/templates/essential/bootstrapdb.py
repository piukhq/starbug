from starbug.kube.common import Metadata
from starbug.kube.job import Job, JobSpec, JobTemplate, JobTemplateSpec
from starbug.kube.pod import Container, ImagePullSecrets


class BootstrapDB:
    """Defines a Bootstrap DB Instance."""

    def __init__(self, namespace: str) -> None:
        """Initialize the BootstrapDB Class."""
        self.namespace = namespace
        self.name = "bootstrap-db"
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
                                image="binkcore.azurecr.io/ait-bootstrap-db:latest",
                            ),
                        ],
                        image_pull_secrets=[
                            ImagePullSecrets(name="binkcore.azurecr.io"),
                        ],
                    ),
                ),
            ),
        )
        self.all = [self.job]
