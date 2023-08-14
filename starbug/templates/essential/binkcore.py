from starbug.kube.secret import Secret
from starbug.kube.common import Metadata


class Binkcore:
    """Defines a Binkcore Secret."""

    def __init__(self, namespace: str) -> None:
        """Initialize the Binkcore Class."""
        self.namespace = namespace
        self.name = "binkcore.azurecr.io"
        self.secret = Secret(
            metadata=Metadata(
                name=self.name,
                namespace=self.namespace,
            ),
            type="kubernetes.io/dockerconfigjson",
            data={
                ".dockerconfigjson": "eyJhdXRocyI6IHsiYmlua2NvcmUuYXp1cmVjci5pbyI6IHsidXNlcm5hbWUiOiAiYmlua2NvcmUiLCAicGFzc3dvcmQiOiAiaVpJRG05NEU0Uz1pWTZZWWVXSjRKNkk5UXNSbllqaUsiLCAiZW1haWwiOiAiZGV2b3BzQGJpbmsuY29tIiwgImF1dGgiOiAiWW1sdWEyTnZjbVU2YVZwSlJHMDVORVUwVXoxcFdUWlpXV1ZYU2pSS05razVVWE5TYmxscWFVcz0ifX19",  # noqa: E501
            },
        )

    def __iter__(self) -> list:
        """Return all Objects as a list."""
        yield from [self.secret]
